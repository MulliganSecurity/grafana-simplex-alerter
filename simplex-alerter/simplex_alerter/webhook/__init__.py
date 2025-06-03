import json
import aiohttp
from simplex_alerter.config import get_config
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from observlib import traced
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from functools import lru_cache
from opentelemetry.metrics import get_meter
from opentelemetry import trace
from simpx.client import ChatClient
from simpx.command import GroupProfile,ChatType,ComposedMessage
from logging import getLogger
from .request_models import Alert

service_name = None


app = FastAPI()


simplex_endpoint = None


def set_sname(name):
    global service_name
    service_name = name

@lru_cache(maxsize = None)
def get_counter(counter_data):
    return get_meter(service_name).create_counter(**dict(counter_data))

@lru_cache(maxsize = None)
def get_timer(timer_data):
    return get_meter(service_name).create_histogram(**dict(timer_data))

def label_fn(result, error):
    if error.status_code >= 400 and error.status_code <= 400:
        return {"status":"4xx"}
    result.render()
    data = json.loads(result.body.decode())
    return {"target_group":data["group"]}

traced_conf = {
        "counter" : "webhook_calls",
        "counter_factory" : get_counter,
        "tracer" : service_name,
        "label_fn": label_fn
        }


def get_app():
    global app
    return app

def set_endpoint(endpoint):
    global simplex_endpoint
    simplex_endpoint = endpoint


@app.on_event("startup")
@traced(tracer = traced_conf["tracer"], timing_histogram = {"name":"execution_timer","unit":"ms","description":"function execution duration"}, timer_factory = get_timer )
async def startup_event():
    global simplex_endpoint
    span = trace.get_current_span()
    l = getLogger(service_name)

    span.add_event("initializing client",attributes = {"endpoint":simplex_endpoint})
    l.info("initializing client",extra = {"endpoint":simplex_endpoint})
    client = await ChatClient.create(simplex_endpoint)
    config = get_config()

    span.add_event("retrieving connected groups")
    group_data = await client.api_get_groups()
    groups = {}
    span.add_event("identified groups",attributes = {"groups":json.dumps(groups)})

    if len(group_data["groups"]) > 0:
        for g in group_data["groups"][0]:
            if "groupProfile" in g:
                groups[g["groupProfile"]["displayName"]] = g["groupId"]
            else:
                continue

    for group in config["alert_groups"]:
        if group["name"] in groups.keys():
            continue

        if "invite_link" in group:
            l.info("joining group", extra = { "group":group["name"]})
            span.add_event("joining group",attributes = {"message": "joining group", "group":group["name"]})
            await client.api_connect(group["invite_link"])
    app.state.simpleX = client
    app.state.groups = groups



@app.on_event("shutdown")
@traced(tracer = traced_conf["tracer"])
async def shutdown_event():
    pass

@app.get("/metrics")
@traced(counter ="metrics_calls", counter_factory = get_counter)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/{endpoint:path}")
@traced(**traced_conf)
async def post_message(endpoint: str,alert: Alert):
    chatId = app.state.groups.get(endpoint)

    if not chatId:
        raise HTTPException(status_code=404)

    await app.state.simpleX.api_send_text_message(ChatType.Group, chatId, f"{alert.title}\n{alert.message}")
    return JSONResponse(content=json.dumps({"status":"message sent","target_group":endpoint}))

FastAPIInstrumentor().instrument_app(app)

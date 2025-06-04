import json
from simplex_alerter.config import get_config
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from observlib import traced
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from functools import lru_cache
from opentelemetry.metrics import get_meter
from opentelemetry import trace
from simpx.client import ChatClient
from simpx.command import ChatType
from logging import getLogger
from .request_models import Alert

service_name = "simpleX-alerter"


app = FastAPI()


simplex_endpoint = None


@lru_cache(maxsize=None)
def get_counter(counter_data):
    return get_meter(service_name).create_counter(**dict(counter_data))


@lru_cache(maxsize=None)
def get_timer(timer_data):
    return get_meter(service_name).create_histogram(**dict(timer_data))


def label_fn(result, error):
    if error:
        if error.status_code >= 400 and error.status_code <= 500:
            return {"status": "4xx"}
        else:
            return {"status": "5xx"}
    if result:
        res = json.loads(result.body)
        return res
    return {}


traced_conf = {
    "counter": "webhook_calls",
    "counter_factory": get_counter,
    "tracer": service_name,
    "label_fn": label_fn,
}


def get_app():
    global app
    return app


def set_endpoint(endpoint):
    global simplex_endpoint
    simplex_endpoint = endpoint


async def get_groups(group_data):
    groups = {}
    if len(group_data["groups"]) > 0:
        for group_data_entry in group_data["groups"]:
            if "groupProfile" in group_data_entry[0]:
                groups[group_data_entry[0]["groupProfile"]["displayName"]] = (
                    group_data_entry[0]["groupId"]
                )
    return groups


@app.on_event("startup")
@traced(
    tracer=traced_conf["tracer"],
    timing_histogram={
        "name": "execution_timer",
        "unit": "ms",
        "description": "function execution duration",
    },
    timer_factory=get_timer,
)
async def startup_event():
    global simplex_endpoint
    span = trace.get_current_span()
    logger = getLogger(service_name)

    span.add_event("initializing client", attributes={"endpoint": simplex_endpoint})
    logger.info("initializing client", extra={"endpoint": simplex_endpoint})
    client = await ChatClient.create(simplex_endpoint)
    config = get_config()

    groups = await get_groups(await client.api_get_groups())
    for group in config["alert_groups"]:
        if group["name"] in groups.keys():
            continue

        if "invite_link" in group:
            logger.info("joining group", extra={"group": group["name"]})
            span.add_event(
                "joining group",
                attributes={"message": "joining group", "group": group["name"]},
            )
            await client.api_connect(group["invite_link"])


@app.on_event("shutdown")
@traced(tracer=traced_conf["tracer"])
async def shutdown_event():
    pass


@app.get("/metrics")
@traced(
    tracer=traced_conf["tracer"], counter="metrics_calls", counter_factory=get_counter
)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/{endpoint:path}")
@traced(**traced_conf)
async def post_message(endpoint: str, alert: Alert):
    span = trace.get_current_span()
    logger = getLogger(service_name)
    global simplex_endpoint
    span.add_event("creating client")
    client = await ChatClient.create(simplex_endpoint)
    span.add_event("getting latest groups")
    groups = await get_groups(await client.api_get_groups())
    chatId = groups.get(endpoint)

    if not chatId:
        logger.error(f"chat group {endpoint} not found")
        span.add_event("group not found")
        raise HTTPException(status_code=404)

    span.add_event("sending message")
    logger.info(
        "sending message", extra={"alert": alert.message, "target_group": endpoint}
    )
    await client.api_send_text_message(
        ChatType.Group, chatId, f"{alert.title}\n{alert.message}"
    )
    return JSONResponse(content={"status": "message sent", "target_group": endpoint})


FastAPIInstrumentor().instrument_app(app)

import json
from typing import Union
from simplex_alerter.config import get_config
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from observlib import traced
from fastapi import FastAPI, HTTPException, Response, Request
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from functools import lru_cache
from opentelemetry.metrics import get_meter
from opentelemetry import trace
from simplex_alerter.simpx.client import ChatClient
from simplex_alerter.simpx.command import ChatType
from logging import getLogger
from .request_models import KnownModels

service_name = "simpleX-alerter"


app = FastAPI()


simplex_endpoint = None


@lru_cache(maxsize=None)
def get_counter(counter_data):
    return get_meter(service_name).create_counter(**dict(counter_data))


@lru_cache(maxsize=None)
def get_timer(timer_data):
    return get_meter(service_name).create_histogram(**dict(timer_data))


def label_fn(result, error, func_args, func_kwargs=None):
    result = {"group": func_args[0], "alert_type": func_args[1]}
    if error:
        code_family = error.status_code // 100
        result |= {"status": f"{code_family}xx"}
    return result


traced_conf = {
    "counter": "webhook_calls",
    "counter_factory": get_counter,
    "tracer": service_name,
    "label_fn": label_fn,
    "func_name_as_label": True,
}

endpoint_group_map = {}


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
    timer={
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
    logger.info("groups from client",extra = {"groups": groups})
    logger.info("groups from config", extra = {"goups":config["alert_groups"]})
    for group in config["alert_groups"]:
        if group["endpoint_name"] in groups.keys():
            continue
        custom_group_name = group.get("group_name")
        if custom_group_name:
            endpoint_group_map[group["endpoint_name"]] = custom_group_name
        else:
            custom_group_name = group["endpoint_name"]

        if "invite_link" in group:
            logger.info("joining group", extra={"group": custom_group_name})
            span.add_event(
                "joining group",
                attributes={"message": "joining group", "group": custom_group_name},
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
async def post_message(
    endpoint: str, request: Request, alert: Union[KnownModels, dict]
):
    span = trace.get_current_span()
    logger = getLogger(service_name)
    global simplex_endpoint
    span.add_event("creating client")
    client = await ChatClient.create(simplex_endpoint)
    span.add_event("getting latest groups")
    groups = await get_groups(await client.api_get_groups())

    custom_group_name = endpoint_group_map.get(endpoint)
    if custom_group_name:
        chatId = groups.get(custom_group_name)
    else:
        chatId = groups.get(endpoint)

    body = await request.body()
    body = body.decode()
    logger.info(f"received message {body}")

    if not chatId:
        logger.error(f"chat group {endpoint} not found")
        span.add_event("group not found")
        raise HTTPException(status_code=404)

    span.add_event("sending message")

    if isinstance(alert, KnownModels):
        msg = await alert.render()
        logger.info(
            "sending alert",
            extra={"alert": msg, "target_group": endpoint},
        )
        await client.api_send_text_message(ChatType.Group, chatId, msg)
    else:
        logger.info("unknown alert model, sending raw json", extra={"content": alert})
        await client.api_send_text_message(
            ChatType.Group, chatId, json.dumps(alert, indent=4)
        )

    return Response()


FastAPIInstrumentor().instrument_app(app)

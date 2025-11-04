import json
import pickle
import aiofiles
from datetime import datetime, timedelta
import errno
from builtins import ConnectionRefusedError
import subprocess
import asyncio
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
from simplex_alerter.config import CONNECTION_ATTEMPTS
from simplex_alerter.simpx.command import ChatType
from logging import getLogger
from .request_models import KnownModels
from simplex_alerter.chat import monitor_channels, deadmans_switch_notifier

service_name = "simpleX-alerter"


app = FastAPI()


simplex_endpoint = None
db_path = None


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

def set_db_path(folder):
    global db_path
    db_path = folder

async def get_groups(group_data):
    groups = {}
    if len(group_data["groups"]) > 0:
        for group_data_entry in group_data["groups"]:
            if "groupProfile" in group_data_entry[0]:
                groups[group_data_entry[0]["groupProfile"]["displayName"]] = (
                    group_data_entry[0]["groupId"]
                )
    return groups

async def load_liveness_data(config):
    data_path = "/alerterconfig/ddms.pickle"
    user_liveness_data = {} 
    try:
        async with aiofiles.open(data_path, "rb") as fh:
            pickled = await fh.read()
            user_liveness_data = pickle.loads(pickled)
    except OSError as e:
        if e.errno == errno.ENOENT:
            #no existing file
            pass
        else:
            raise

    sw_config = config.get("deadmans_switch")
    if sw_config:
        for user, alert_config in sw_config.items():
            alert_config["alert_threshold_seconds"] = timedelta(seconds = alert_config["alert_threshold_seconds"])
            alert_config["trigger_threshold_seconds"] = timedelta(seconds = alert_config["trigger_threshold_seconds"])
            if user in user_liveness_data:
                user_liveness_data[user] |= alert_config #update alert thresholds if required
            else:
                user_liveness_data[user] = alert_config
            if "last_seen" not in user_liveness_data[user]:
                user_liveness_data[user]["last_seen"] = datetime.now()
            if "alert_sent" not in user_liveness_data[user]:
                user_liveness_data[user]["alert_sent"] = False
            if "switch_triggered" not in user_liveness_data[user]:
                user_liveness_data[user]["switch_triggered"] = False
    return user_liveness_data


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
    host_port = simplex_endpoint.split(':')
    logger = getLogger(service_name)
    logger.info("starting chat client on {}".format(host_port[2]))
    subprocess.Popen(
        ["simplex-chat", "-y", "-p", host_port[2], "-d", db_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


    span = trace.get_current_span()

    span.add_event("initializing client", attributes={"endpoint": simplex_endpoint})
    logger.info("initializing client", extra={"endpoint": simplex_endpoint})
    while True:
        try:
            client = await ChatClient.create(simplex_endpoint)
            break
        except ConnectionRefusedError:
            logger.info("waiting for the chat client to connect")
            await asyncio.sleep(1)

    logger.info("retrieving config")
    config = get_config()

    logger.info("starting channel monitor for deadman's switch capabilities")
    span.add_event("starting listener routine")
    loop = asyncio.get_running_loop()
    liveness_data = await load_liveness_data(config)
    loop.create_task(monitor_channels(liveness_data,client))
    loop.create_task(deadmans_switch_notifier(liveness_data,client))

    logger.info("retrieving groups")
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
            attempts = 0
            while attempts < CONNECTION_ATTEMPTS:
                try:
                    logger.info(f"attempting join on {custom_group_name}")
                    await client.api_connect(group["invite_link"])
                    logger.info(f"joined group {custom_group_name}")
                    break
                except:
                    logger.info("waiting for 5 seconds before retrying join")
                    await asyncio.sleep(5)
                    attempts += 1


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

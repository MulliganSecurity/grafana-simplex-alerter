import aiohttp
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from observlib import traced
from aiohttp_socks import ProxyConnector
from fastapi import FastAPI, Request,Response
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from functools import lru_cache
from opentelemetry.metrics import get_meter
import logging as l
from .simpleXClient import Client

service_name = None


app = FastAPI()

local = False

simplex_endpoint = None


def set_sname(name):
    global service_name
    service_name = name

@lru_cache(maxsize = None)
def get_counter(name):
    return get_meter(service_name).create_counter(name)

traced_conf = {
        "success_counter" : "webhook_call_success",
        "failure_counter" : "webhook_call_failure",
        "counter_factory" : get_counter,
        "tracer" : service_name,
        }

def set_local(mode):
    global local
    local = mode


def get_app():
    global app
    return app

def set_endpoint(endpoint):
    global simplex_endpoint
    simplex_endpoint = endpoint


@app.on_event("startup")
@traced(tracer = traced_conf["tracer"])
async def startup_event():
    proxy = None
    if not local:
        proxy = ProxyConnector.from_url("socks5://127.0.0.1:9050")

    app.state.simpleX = Client(simplex_endpoint, proxy)


@app.on_event("shutdown")
@traced(tracer = traced_conf["tracer"])
async def shutdown_event():
    await app.state.aiohttp_session.close()

@traced(**(traced_conf | {"success_counter":"metrics_call_success","failure_counter":"metrics_call_failure", "timing_histogram" : None}))
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/")
@traced(**traced_conf)
async def post_message(message):
    return Response("hello")

FastAPIInstrumentor().instrument_app(app)

import aiohttp
from observlib import traced, get_trace
from aiohttp_socks import ProxyConnector
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()

local = False

simplex_endpoint = None


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
@traced
async def startup_event():
    span = get_trace().get_current_span()
    if local:
        session = aiohttp.ClientSession()
    else:
        session = aiohttp.ClientSession(
            connector=ProxyConnector.from_url("socks5://127.0.0.1:9050"),
        )
    app.state.ws_connection = session.ws_connect(simplex_endpoint)


@app.on_event("shutdown")
@traced
async def shutdown_event():
    await app.state.aiohttp_session.close()


FastAPIInstrumentor().instrument_app(app)

from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

AioHttpClientInstrumentor().instrument()

from client import Client as Client

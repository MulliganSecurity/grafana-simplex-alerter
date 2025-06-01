from opentelemetry import metrics
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

AioHttpClientInstrumentor().instrument()


metrics = None


def get_metrics():
    global metrics
    return metrics


def configure_metrics():
    global metrics
    meter = metrics.get_meter("simplex-alerter")
    metrics = {
        "successful_calls": meter.create_counter(
            name="simplex_alerter_calls_success",
            unit="1",
            description="alerter webhook calls",
        ),
        "failed_calls": meter.create_counter(
            name="simplex_alerter_calls_errors",
            unit="1",
            description="alerter webhook calls errors",
        ),

        "ws_messages": meter.create_counter(
            name="simplex_alerter_wsmessage_sent",
            unit="1",
            description="messages sent to simpleX chat server",
        ),
    }

from observlib import get_meter


metrics = None


def get_metrics():
    global metrics
    return metrics


def configure_metrics():
    global metrics
    meter = get_meter()
    metrics = {
        "calls": meter.create_counter(
            name="simplex_alerter_calls",
            unit="1",
            description="alerter webhook calls",
        ),
        "ws_messages": meter.create_counter(
            name="simplex_alerter_wsmessage_sent",
            unit="1",
            description="messages sent to simpleX chat server",
        ),
    }

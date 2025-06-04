from .webhook import get_app, set_endpoint
import uvicorn
import argparse
from observlib import configure_telemetry
from .config import generate_config, load_config


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--opentelemetry",
        action="store",
        help="opentelemetry server",
        dest="otel_server",
        default=None,
    )
    parser.add_argument(
        "-f",
        "--profiling",
        action="store",
        help="pyroscope server address for profiling",
        dest="pyroscope_server",
        default=None,
    )
    parser.add_argument(
        "-b",
        "--bind-addr",
        action="store",
        help="host:port to run the app on",
        dest="bind_addr",
        default="127.0.0.1:7898",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="enable debug mode, increases pyroscope sampling rate if configured",
        dest="debug",
    )

    parser.add_argument(
        "-c",
        "--config",
        action="store",
        help="config file",
        dest="config",
    )

    parser.add_argument(
        "-g",
        "--generate-config",
        action="store_true",
        help="generate config file with placeholder values",
        dest="gen_config",
    )

    parser.add_argument(
        "-e",
        "--endpoint",
        action="store",
        help="simplex endpoint",
        default="127.0.0.1:7897",
        dest="endpoint",
    )

    args = parser.parse_args()

    if args.gen_config:
        generate_config()
        return
    if not args.config:
        print("config file required")
        return

    sname = "simpleX-alerter"
    load_config(args.config)

    configure_telemetry(
        sname,
        args.otel_server,
        args.pyroscope_server,
        args.debug,
    )

    [host, port] = args.bind_addr.split(":")

    set_endpoint(f"ws://{args.endpoint}")
    app = get_app()
    uvicorn.run(app, host=host, port=int(port))

from .webhook import get_app, set_endpoint, set_db_path
import uvicorn
import argparse
from observlib import configure_telemetry
from .config import load_config
from .chat import init_chat


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
        "-D",
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
        "-e",
        "--endpoint",
        action="store",
        help="simplex endpoint",
        default="127.0.0.1:7897",
        dest="endpoint",
    )

    parser.add_argument(
        "-p",
        "--profile-name",
        action="store",
        help="simplex bot name",
        default="alertBot",
        dest="profile",
    )

    parser.add_argument(
        "-d",
        "--db-path",
        action="store",
        help="path for chatdb",
        default="/alerterconfig/chatDB",
        dest="db_path",
    )


    args = parser.parse_args()

    if not args.config:
        print("config file required")
        return

    sname = "simpleX-alerter"
    load_config(args.config)

    sample_rate = 5
    attrs = {}
    if args.debug:
        sample_rate = 100
        attrs = {"environment":"dev"}

    configure_telemetry(
        sname,
        args.otel_server,
        args.pyroscope_server,
        sample_rate,
        resource_attrs = attrs,
    )

    init_chat(args.profile, args.db_path)

    [host, port] = args.bind_addr.split(":")

    set_endpoint(f"ws://{args.endpoint}")
    set_db_path(args.db_path)
    app = get_app()
    uvicorn.run(app, host=host, port=int(port))

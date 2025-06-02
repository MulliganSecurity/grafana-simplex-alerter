from .webhook import get_app, set_local, set_endpoint, set_sname
import uvicorn
from time import sleep
import argparse
from observlib import configure_telemetry
from .config import generate_config, load_config

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--address",
        action="store",
        dest="addr",
        default="127.0.0.1",
        help="bind address",
    )
    parser.add_argument("-m","--metrics", action = "store", dest = "prometheus_config", default = "127.0.0.1:0", help = "interface and port to expose legacy prometheus metrics, port to 0 to disable, default 127.0.0.1:0")
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
        "-p",
        "--port",
        action="store",
        help="port to run the app on",
        dest="port",
        default = 8080,
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="enable debug mode, increases pyroscope sampling rate if configured",
        dest="debug",
    )

    parser.add_argument(
        "-l",
        "--local",
        action="store_true",
        help="enable local mode, simplex connections won't be run through tor",
        dest="local",
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
        action="store",
        help="generate config file with placeholder values",
        dest="gen_config",
    )

    parser.add_argument(
        "-s",
        "--simplex-ws-server",
        action="store",
        help="simplex server for alerting",
        default = "127.0.0.1:5353",
        dest="gen_config",
    )

    parser.add_argument(
        "-e",
        "--endpoint",
        action="store",
        help="endpoint to receive webhook calls (default 127.0.0.1:7897)",
        default = "127.0.0.1:7897",
        dest="endpoint",
    )


    args = parser.parse_args()
    sname = "simpleX-alerter"

    configure_telemetry(
        sname,
        args.otel_server,
        args.pyroscope_server,
        args.debug,
    )

    [host, port] = args.endpoint.split(":")

    set_local(args.local)
    set_sname(sname)
    set_endpoint(f"http://{args.endpoint}")
    app = get_app()
    uvicorn.run(app, host=host, port=int(port))

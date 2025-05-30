def import argparse
from observlib import configure_telemetry
from .config import generate_config, load_config

def run():
    parser.add_argument(
        "-a",
        "--address",
        action="store",
        dest="addr",
        default="127.0.0.1",
        help="bind address",
    )
    parser.add_argument(
        "-p", "--port", default=8080, action="store", dest="port", help="bind port"
    )
    parser.add_argument("-m","--metrics", action = "store", dest = "prometheus_port", default = "127.0.0.1:0", help = "interface and port to expose legacy prometheus metrics, 0 to disable")
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
        "-d",
        "--debug",
        action="store_true",
        help="enable debug mode, increase telemetry sampling rate",
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
        action="store",
        help="generate config file with placeholder values",
        dest="gen_config",
    )

    parser.add_argument(
        "-s",
        "--simplex-ws-server",
        action="store",
        help="simplex server for alerting"
        default = "127.0.0.1:5353"
        dest="gen_config",
    )

    args = parser.parse_args()

    if args.otel_server and args.pyroscope_server:
        configure_telemetry(
            "b2r2-licence-server",
            args.otel_server,
            args.pyroscope_server,
            devMode=args.debug,
        )


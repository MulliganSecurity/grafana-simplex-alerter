import yaml

CONFIG = {}
CONNECTION_ATTEMPTS = 5

DEFAULT_CONFIG = {
    "alert_groups": [
        {
            "name": "alert_group0",
            "invite_link": "https://simplex.chat/contact#/?v=2-7&sm...",
        },
    ],
}


def load_config(filename):
    global CONFIG
    with open(filename) as fh:
        CONFIG = yaml.safe_load(fh.read())


def get_config():
    global CONFIG
    return CONFIG

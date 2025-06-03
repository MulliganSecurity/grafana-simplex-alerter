import yaml

CONFIG = {}

DEFAULT_CONFIG = {
        "alert_groups" : [
                {
                    "name":"azer",
                    "invite_link":"https://simplex.chat/contact#/?v=2-7&smp=smp%3A%2F%2F1OwYGt-yqOfe2IyVHhxz3ohqo3aCCMjtB-8wn4X_aoY%3D%40smp11.simplex.im%2FRGI_Vi6jfnUiMA9HW1XxDcTS5wGaVAtw%23%2F%3Fv%3D1-4%26dh%3DMCowBQYDK2VuAyEATJyIORSqQTkyGeZ8XqzurFxqgsZUkyPF_7U2p_xr820%253D%26q%3Dc%26srv%3D6ioorbm6i3yxmuoezrhjk6f6qgkc4syabh7m3so74xunb5nzr4pwgfqd.onion&data=%7B%22groupLinkId%22%3A%22sSBJuqOfJt8x-1QSsqieNQ%3D%3D%22%7D",
                },
            ],
        }
def generate_config():
    print(yaml.dump(DEFAULT_CONFIG))


def load_config(filename):
    global CONFIG
    with open(filename) as fh:
        CONFIG = yaml.safe_load(fh.read())

def get_config():
    global CONFIG
    return CONFIG

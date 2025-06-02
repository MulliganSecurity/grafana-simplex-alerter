import aiohttp

class Client():
    def __init__(self, endpoint, proxy = None):
        self.session = aiohttp.ClientSession(
            connector = proxy,
        )

        self.ws_connection = self.session.ws_connect(endpoint)



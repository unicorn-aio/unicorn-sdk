import requests


class UnicornSdk:
    ACCESS_TOKEN: str

    def __init__(self, access_token=None, api_url="https://us.unicorn-bot.com", debug=False):
        self.api_url = api_url
        self._api_client = requests.Session()
        if access_token:
            UnicornSdk.ACCESS_TOKEN = access_token
        self._debug = debug

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(UnicornSdk, cls).__new__(cls)
        return cls._instance

    def _get_api_client(self):
        return self._api_client

    def _get_authorization(self):
        return {
            "Authorization": "Bearer " + self.ACCESS_TOKEN
        }

    def _get_proxys_for_sdk(self):
        cur_proxyuri = "http://127.0.0.1:8888"
        proxies = {
            "http": cur_proxyuri,
            "https": cur_proxyuri,
        }
        return proxies if self._debug else None

    @classmethod
    def auth(cls, access_token):
        cls.ACCESS_TOKEN = access_token

    def create_device_session(self, session_id, platform):
        """
        create new DeviceSession
        :return:
        """
        pass

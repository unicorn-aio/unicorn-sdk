import requests


class UnicornSdk:
    CONFIG = {
        "access_token": None,
        "sdk_proxy": "http://127.0.0.1:8888",
        "api_url": "https://us.unicorn-bot.com",
        "is_debug": False,
    }
    API_CLIENT = requests.Session()

    def __init__(self):
        self._debug = False

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(UnicornSdk, cls).__new__(cls)
        return cls._instance

    def _get_api_client(self):
        return UnicornSdk.API_CLIENT

    @property
    def api_url(self):
        return UnicornSdk.CONFIG["api_url"]

    @property
    def is_debug(self):
        return UnicornSdk.CONFIG["is_debug"]

    def _get_authorization(self):
        return {
            "Authorization": "Bearer " + str(UnicornSdk.CONFIG["access_token"])
        }

    def _get_proxys_for_sdk(self):
        cur_proxyuri = UnicornSdk.CONFIG["sdk_proxy"]
        proxies = {
            "http": cur_proxyuri,
            "https": cur_proxyuri,
        }
        return proxies if self.is_debug else None

    @classmethod
    def auth(cls, access_token):
        UnicornSdk.CONFIG["access_token"] = access_token

    def create_device_session(self, session_id, platform):
        """
        create new DeviceSession
        :return:
        """
        pass

    @classmethod
    def config_sdk(cls, access_token=None, debug=None, api_url=None):
        if access_token:
            UnicornSdk.CONFIG["access_token"] = access_token
        if debug is not None:
            UnicornSdk.CONFIG["is_debug"] = bool(debug)
        if api_url:
            UnicornSdk.CONFIG["api_url"] = api_url
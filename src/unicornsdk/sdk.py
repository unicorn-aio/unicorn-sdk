import atexit

import requests

from unicornsdk.api.captcha import CaptchaAPI
from unicornsdk.api.devicesession import DeviceSession

class UnicornSdk:
    CONFIG = {
        "access_token": None,
        "sdk_proxy": None,
        "api_url": "https://us.unicorn-bot.com",
        "is_debug": False,
        "timeout": 30,
    }

    API_CLIENT = requests.Session()

    def __init__(self):
        self._debug = False

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(UnicornSdk, cls).__new__(cls)
        return cls._instance

    def _get_api_client(self):
        return self.API_CLIENT

    @property
    def api_url(self):
        return UnicornSdk.CONFIG["api_url"]

    @property
    def timeout(self):
        return UnicornSdk.CONFIG.get("timeout", 60)

    @property
    def is_debug(self):
        return UnicornSdk.CONFIG["is_debug"]

    def _get_authorization(self):
        if not UnicornSdk.CONFIG.get("access_token"):
            raise Exception("you need set access_token first! ")
        return {
            "Authorization": "Bearer " + str(UnicornSdk.CONFIG["access_token"])
        }

    def _get_proxys_for_sdk(self) -> object:
        cur_proxyuri = UnicornSdk.CONFIG["sdk_proxy"]
        proxies = {
            "http": cur_proxyuri,
            "https": cur_proxyuri,
        }
        return proxies if self.is_debug else None

    @classmethod
    def auth(cls, access_token):
        UnicornSdk.CONFIG["access_token"] = access_token

    @classmethod
    def create_device_session(cls, session_id, platform):
        """
        create new DeviceSession
        :return:
        """
        return DeviceSession(UnicornSdk(), session_id=session_id, platform=platform)

    @classmethod
    def config_sdk(cls, access_token=None, debug=None, api_url=None):
        if access_token:
            cls.CONFIG["access_token"] = access_token
        if debug is not None:
            cls.CONFIG["is_debug"] = bool(debug)
        if api_url:
            cls.CONFIG["api_url"] = api_url

    @classmethod
    def captcha_api(cls) -> "CaptchaAPI":
        return CaptchaAPI(sdk=UnicornSdk())

    @classmethod
    def on_exit(cls):
        if cls.API_CLIENT:
            cls.API_CLIENT.close()


atexit.register(UnicornSdk.on_exit)

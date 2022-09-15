import asyncio
import atexit

import aiohttp

from unicornsdk.sdk import UnicornSdk
from unicornsdk_async.api.captcha import CaptchaAPI
from unicornsdk_async.api.devicesession import DeviceSession

DEFAULT_CONCURRENCY_SEMAPHORE = 1000

class UnicornSdkAsync(UnicornSdk):
    API_CLIENT: aiohttp.ClientSession = None
    CONCURRENCY_SEMAPHORE: asyncio.Semaphore


    def __init__(self):
        super().__init__()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance_async'):
            cls._instance_async = object.__new__(cls)
        return cls._instance_async

    @classmethod
    def config_sdk(cls, access_token=None, debug=None, api_url=None, max_concurrency=None):
        if max_concurrency:
            cls.CONFIG["max_concurrency"] = max_concurrency
        super().config_sdk(access_token, debug, api_url)

    def _get_proxys_for_sdk(self) -> object:
        cur_proxyuri = UnicornSdk.CONFIG["sdk_proxy"]
        return cur_proxyuri if self.is_debug else None

    @classmethod
    def create_device_session(cls, session_id, platform):
        """
        create new DeviceSession
        :return:
        """
        return DeviceSession(UnicornSdkAsync(), session_id=session_id, platform=platform)

    @classmethod
    def captcha_api(cls) -> CaptchaAPI:
        return CaptchaAPI(UnicornSdk())

    @classmethod
    async def init(cls):
        """
        call it in async event loop
        :return:
        """
        if not UnicornSdkAsync.API_CLIENT:
            conn = aiohttp.TCPConnector(limit=None, ssl=False)
            UnicornSdkAsync.API_CLIENT = aiohttp.ClientSession(connector=conn)
        if not hasattr(cls, 'CONCURRENCY_SEMAPHORE'):
            UnicornSdkAsync.CONCURRENCY_SEMAPHORE = asyncio.Semaphore(cls.CONFIG.get("max_concurrency") or DEFAULT_CONCURRENCY_SEMAPHORE)

    @classmethod
    async def deinit(cls):
        """
        call it in async event loop
        :return:
        """
        if cls.API_CLIENT:
            await cls.API_CLIENT.close()

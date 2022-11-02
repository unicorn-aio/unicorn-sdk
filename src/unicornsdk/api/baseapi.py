import logging
from typing import TYPE_CHECKING

from tenacity import retry, stop_after_attempt, wait_exponential, before_log

from loguru import logger

if TYPE_CHECKING:
    from unicornsdk.api.devicesession import DeviceSession
    from unicornsdk.sdk import UnicornSdk

class BaseApi:
    def __init__(self, sdk: "UnicornSdk"):
        self._sdk = sdk

    @retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=10), before=before_log(logger, logging.DEBUG))
    def get(self, url, **kwargs):
        client = self._sdk._get_api_client()
        resp = client.get(
            url,
            **kwargs,
            verify=False,
            proxies=self._sdk._get_proxys_for_sdk(),
            timeout=self._sdk.timeout
        )
        return resp

    @retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=10), before=before_log(logger, logging.DEBUG))
    def post(self, url, **kwargs):
        client = self._sdk._get_api_client()
        resp = client.post(
            url,
            **kwargs,
            verify=False,
            proxies=self._sdk._get_proxys_for_sdk(),
            timeout=self._sdk.timeout
        )
        return resp

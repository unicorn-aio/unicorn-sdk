import logging
from typing import TYPE_CHECKING

import requests.exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, before_log, retry_if_exception_type

from loguru import logger

from unicornsdk import exceptions

if TYPE_CHECKING:
    from unicornsdk.api.devicesession import DeviceSession
    from unicornsdk.sdk import UnicornSdk

class BaseApi:
    def __init__(self, sdk: "UnicornSdk", device_session: "DeviceSession"):
        self._sdk = sdk
        self.device_session = device_session

    @retry(reraise=True,
           stop=stop_after_attempt(3),
           before=before_log(logger, logging.DEBUG),
           retry=retry_if_exception_type(requests.exceptions.Timeout)
           )
    def request(self, fn, url, **kwargs):
        resp = fn(
            str(url),
            headers=self._sdk._get_authorization(),
            **kwargs,
            verify=False,
            cookies=self.device_session.get_cookie(),
            proxies=self._sdk._get_proxys_for_sdk(),
            timeout=self._sdk.timeout
        )
        if resp.status_code == 200:
            return resp
        elif resp.status_code == 400:
            raise exceptions.ParamsError(resp.text)
        elif resp.status_code == 403:
            raise exceptions.NoAuthenticated(resp.text)
        else:
            logger.error(resp.text)
            raise Exception(f"{resp.status_code} {resp.text}")

    def get(self, url, **kwargs):
        client = self._sdk._get_api_client()
        return self.request(client.get, url, **kwargs)

    def post(self, url, **kwargs):
        client = self._sdk._get_api_client()
        return self.request(client.post, url, **kwargs)

from typing import TYPE_CHECKING
import base64
import gzip

from loguru import logger

if TYPE_CHECKING:
    from unicornsdk.api.devicesession import DeviceSession
    from unicornsdk.sdk import UnicornSdk


class CaptchaAPI:

    def __init__(self, sdk: "UnicornSdk"):
        self._sdk = sdk

    def image_ocr(self, image:bytes=None, image_path:str=None):
        try:
            if not image:
                if image_path:
                    with open(image_path, "rb") as f:
                        image = f.read()
                else:
                    raise Exception("no image to solve!")

            client = self._sdk._get_api_client()
            resp = client.post(
                self._sdk.api_url + "/api/captcha/image/",
                headers=self._sdk._get_authorization(),
                data=image,
                verify=False,
                proxies=self._sdk._get_proxys_for_sdk(),
            )

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 403:
                raise Exception("Not Authenticated")
            else:
                raise Exception(resp.text)
        except Exception as e:
            logger.error(repr(e))
            raise e

from typing import TYPE_CHECKING
import base64
import gzip

from loguru import logger

if TYPE_CHECKING:
    from unicornsdk.api.devicesession import DeviceSession
    from unicornsdk.sdk import UnicornSdk


class KasadaAPI:

    def __init__(self, sdk: "UnicornSdk", device_session: "DeviceSession"):
        self.device_session = device_session
        self.sdk = sdk

    def kpsdk_answer(self, x_kpsdk_ct, x_kpsdk_st, st_diff, x_kpsdk_cr=True):
        try:
            param = {
                "x_kpsdk_ct": x_kpsdk_ct,
                "x_kpsdk_cr": x_kpsdk_cr,
                "x_kpsdk_st": x_kpsdk_st,
                "st_diff": st_diff,
            }
            client = self.sdk._get_api_client()
            resp = client.post(
                self.sdk.api_url + "/api/kpsdk/answer/",
                headers=self.sdk._get_authorization(),
                cookies=self.device_session.get_cookie(),
                json=param,
                verify=False,
                proxies=self.sdk._get_proxys_for_sdk()
            )

            if resp.status_code == 200:
                kpparam = resp.json()
                return kpparam
            elif resp.status_code == 403:
                raise Exception("Not Authenticated")
            else:
                logger.error(resp.text)
                raise Exception(resp.text)
        except Exception as e:
            logger.error(repr(e))
            raise e

    def kpsdk_parse_ips(self, ips_url, ips_content, *, host=None, site=None, compress_method="GZIP",
                        proxy_uri=None, cookie=None, cookiename=None):
        try:
            gzipjps = gzip.compress(ips_content)
            client = self.sdk._get_api_client()
            param = {
                "ips_url": ips_url,
                # "host": host,
                "proxy_uri": proxy_uri,
                "compress_method": compress_method,
            }

            resp = client.post(
                self.sdk.api_url + "/api/kpsdk/ips/",
                params=param,
                headers=self.sdk._get_authorization(),
                cookies=self.device_session.get_cookie(),
                files={"ips_js": gzipjps},
                verify=False,
                proxies=self.sdk._get_proxys_for_sdk()
            )

            if resp.status_code == 200:
                kpparam = resp.json()
                tl_body_b64 = kpparam.get("tl_body_b64")
                if tl_body_b64:
                    body = gzip.decompress(base64.b64decode(tl_body_b64))
                    kpparam["body"] = body
                return kpparam
            elif resp.status_code == 403:
                raise Exception("Not Authenticated")
            else:
                logger.error(resp.text)
                raise Exception(resp.text)
        except Exception as e:
            logger.error(repr(e))
            raise e

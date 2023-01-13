from unicornsdk import PlatForm
from unicornsdk.api.kasada import KasadaAPI
from unicornsdk.api.tls import TlsAPI
from unicornsdk.api.datadome import DataDomeAPI


class DeviceSession:

    def __init__(self, sdk, session_id=None, platform=PlatForm.WINDOWS):
        self.sdk = sdk
        self.platform = platform
        self.XSESSIONDATA: str = None
        self.session_id = session_id
        self.device_info = None

    def init_session(self, session_id: str = None, platform: PlatForm = None, flavors=None, **kwargs):
        self.session_id = session_id or self.session_id
        self.platform = platform or self.platform
        url = self.sdk.api_url + "/api/session/init/"
        params = {
            "sessionid": self.session_id,
            "platform": self.platform,
            "flavors": flavors,
            **kwargs,
        }
        resp = self.sdk._get_api_client().post(
            url,
            json=params,
            headers=self.sdk._get_authorization(),
            verify=False,
            proxies=self.sdk._get_proxys_for_sdk()
        )
        if resp.status_code != 200:
            raise Exception(resp.text)
        self.XSESSIONDATA = resp.cookies["XSESSIONDATA"]
        self.device_info = resp.json()
        return self.device_info

    def is_inited(self):
        return bool(self.XSESSIONDATA)

    def get_cookie(self):
        if self.XSESSIONDATA:
            return {
                "XSESSIONDATA": self.XSESSIONDATA
            }
        else:
            return None

    def load_state(self, bundle):
        self.XSESSIONDATA = bundle.get("XSESSIONDATA")
        self.device_info = bundle.get("device_info")

    def save_state(self, bundle):
        bundle["XSESSIONDATA"] = self.XSESSIONDATA
        bundle["device_info"] = self.device_info


    def kasada_api(self, proxy_uri=None):
        return KasadaAPI(self.sdk, self, proxy_uri=proxy_uri)

    def tls_api(self, proxy_uri=None, parrot=None, ja3=None, http2=True, http2Fp=None):
        return TlsAPI(self.sdk, self, proxy_uri=proxy_uri, parrot=parrot, ja3=ja3, http2=http2, http2Fp=http2Fp)

    def datadome_api(self):
        return DataDomeAPI(self.sdk, self)
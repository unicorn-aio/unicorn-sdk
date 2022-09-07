from unicornsdk import PlatForm
from unicornsdk.api.kasada import KasadaAPI
from unicornsdk.api.tls import TlsAPI


class DeviceSession:

    def __init__(self, sdk):
        self.sdk = sdk
        self.XSESSIONDATA: str = None
        self.session_id = None

    def init_session(self, session_id: str, platform: PlatForm, flavors=None, **kwargs):
        self.session_id = session_id
        url = self.sdk.api_url + "/api/session/init/"
        params = {
            "sessionid": session_id,
            "platform": platform,
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

    def get_cookie(self):
        return {
            "XSESSIONDATA": self.XSESSIONDATA
        }

    def kasada_api(self):
        return KasadaAPI(self.sdk, self)

    def tls_api(self, proxy_uri=None, parrot="Chrome100", ja3=None, http2=True):
        return TlsAPI(self.sdk, self, proxy_uri=proxy_uri, parrot=parrot, ja3=ja3, http2=http2)
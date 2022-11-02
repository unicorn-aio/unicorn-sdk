from unicornsdk import PlatForm
from unicornsdk.api.devicesession import DeviceSession as SyncDeviceSession
from unicornsdk_async.api.kasada import KasadaAPI
from unicornsdk_async.api.tls import TlsAPI


class DeviceSession(SyncDeviceSession):


    async def init_session(self, session_id: str = None, platform: PlatForm = None, flavors=None, **kwargs):
        self.session_id = session_id or self.session_id
        self.platform = platform or self.platform
        url = self.sdk.api_url + "/api/session/init/"
        params = {
            "sessionid": self.session_id,
            "platform": self.platform,
            "flavors": flavors,
            **kwargs,
        }
        client = self.sdk._get_api_client()
        async with self.sdk.CONCURRENCY_SEMAPHORE:
            resp = await client.post(
                url,
                json=params,
                headers=self.sdk._get_authorization(),
                ssl=False,
                proxy=self.sdk._get_proxys_for_sdk()
            )
            if resp.status != 200:
                raise Exception(await resp.text())
            self.XSESSIONDATA = resp.cookies["XSESSIONDATA"].value
            self.device_info = await resp.json()
            return self.device_info

    def kasada_api(self, proxy_uri=None):
        return KasadaAPI(self.sdk, self, proxy_uri=proxy_uri)

    def tls_api(self, proxy_uri=None, parrot=None, ja3=None, http2=True, http2Fp=None):
        return TlsAPI(self.sdk, self, proxy_uri=proxy_uri, parrot=parrot, ja3=ja3, http2=http2, http2Fp=http2Fp)

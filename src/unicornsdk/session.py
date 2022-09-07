from typing import TYPE_CHECKING
import re
import uuid
from urllib.parse import urlparse, urljoin

from loguru import logger
import fnmatch
from requests import Session as RequestSession
from unicornsdk import PlatForm
from unicornsdk.api.devicesession import DeviceSession
from unicornsdk.sdk import UnicornSdk
from unicornsdk.utils import infer_platform, accept_language_to_languages, now_time_ms

if TYPE_CHECKING:
    from unicornsdk.api.kasada import KasadaAPI


class Session(RequestSession):

    def __init__(self, session=None):
        super(Session, self).__init__()
        self._device_session: DeviceSession = None
        self._intercept_mapping = {}
        self.sdk = UnicornSdk()
        self._interceptors = {}
        self.session = session

    def init_device_session(self, session_id=None, platform=PlatForm.WINDOWS, **kwargs):
        self._device_session = DeviceSession(self.sdk)
        self._device_session.init_session(
            session_id=session_id or str(uuid.uuid4()),
            platform=platform,
            **kwargs,
        )

    def config_for_kasada(self, intercept_mapping, use_cd=1):
        solver = KasadaSolver(self, intercept_mapping, use_cd=use_cd)
        self._interceptors["kasada"] = solver

    def send(self, request, **kwargs):
        headers = request.headers
        self.infer_device_from_header(headers)
        self.pre_hook(request, **kwargs)
        if self.session:
            # use others session
            r = self.session.send(request, **kwargs)
        else:
            r = super().send(request, **kwargs)
        self.post_hook(r, **kwargs)
        return r

    def pre_hook(self, req, **kwargs):
        for inter_type, solver in self._interceptors.items():
            solver.on_pre(req, **kwargs)

    def post_hook(self, resp, **kwargs):
        for inter_type, solver in self._interceptors.items():
            solver.on_post(resp, **kwargs)

    def infer_device_from_header(self, headers):
        if self._device_session:
            return

        session_id = str(uuid.uuid4())
        ua = headers["user-agent"]
        platform = infer_platform(ua)
        accept_language = headers.get('accept-language')
        languages = accept_language_to_languages(accept_language)
        return self.init_device_session(
            session_id=session_id,
            platform=platform,
            accept_language=accept_language,
            languages=languages,
            ua=ua,
        )


class Solver:

    def __init__(self, session: "Session", intercept_mapping):
        self.session = session
        self.intercept_mapping = intercept_mapping

    def need_solve(self, resp, **kwargs):
        return False

    def solve(resp, **kwargs):
        pass

    def need_inject(self, req, **kwargs):
        parsed_url = urlparse(req.url)
        if parsed_url.netloc in self.intercept_mapping:
            conf = self.intercept_mapping[parsed_url.netloc]
            if req.method in conf:
                for path in conf[req.method]:
                    if fnmatch.fnmatch(parsed_url.path, path):
                        return True
        return False

    def inject(self, req, **kwargs):
        pass

    def on_pre(self, req, **kwargs):
        if self.need_inject(req, **kwargs):
            self.inject(req, **kwargs)

    def on_post(self, resp, **kwargs):
        # should we need solve
        if self.need_solve(resp):
            self.solve(resp, **kwargs)


class KasadaSolver(Solver):

    def __init__(self, *args, use_cd=1, **kwargs):
        super(KasadaSolver, self).__init__(*args, **kwargs)
        self.kasada: "KasadaAPI" = None
        self.use_cd = use_cd
        self.st_diff = None
        self.x_kpsdk_ct = None
        self.x_kpsdk_st = None

    def assume_solver(self):
        if not self.kasada:
            self.kasada = self.session._device_session.kasada_api()

    def need_solve(self, resp, **kwargs):
        if resp.status_code == 429 and resp.text.find("ips.js") != -1:
            return True
        elif resp.status_code == 200 and resp.headers.get("x-kpsdk-ct"):
            # save the updated ct
            self.x_kpsdk_ct = resp.headers.get("x-kpsdk-ct")
        return False

    def solve(self, resp, **kwargs):
        self.assume_solver()

        # got ips.js url
        ips_url = re.match(r".+src=\"(\S+)\".+", resp.text)[1]
        referer = resp.request.url
        ips_url = urljoin(referer, ips_url)
        ipsjs = self.req_ipsjs(ips_url, referer, **kwargs)
        kpparam = self.kasada.kpsdk_parse_ips(ips_url, ipsjs)

        tl_url = urljoin(referer, "/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/tl")
        resp = self.req_tl(tl_url, referer, kpparam, **kwargs)
        if resp.status_code != 200:
            logger.debug(resp.status_code)
            logger.debug(resp.text)
            raise Exception(f"/tl faild! {resp.status_code} {resp.text}")

        self.x_kpsdk_ct = resp.headers["x-kpsdk-ct"]
        self.x_kpsdk_st = resp.headers["x-kpsdk-st"]
        self.st_diff = now_time_ms() - int(self.x_kpsdk_st)

    def inject(self, req, **kwargs):
        self.assume_solver()
        kpparam = self.kasada.kpsdk_answer(self.x_kpsdk_ct, self.x_kpsdk_st, self.st_diff)
        req.headers["x-kpsdk-ct"] = kpparam["x_kpsdk_ct"]
        if self.use_cd == 1:
            req.headers["x-kpsdk-cd"] = kpparam["x_kpsdk_cd"]
        elif self.use_cd == 2:
            req.headers["x-kpsdk-cd"] = kpparam["x_kpsdk_cd2"]

    def req_ipsjs(self, ips_url, referer, **kwargs):
        resp = self.session.get(
            ips_url,
            headers={
                "accept": "*/*",
                "referer": referer,
            },
            **kwargs)
        ipsjs = resp.content
        if len(ipsjs) == 0:
            raise Exception("ips.js length is 0！")
        return ipsjs

    def req_tl(self, tl_url, referer, kpparam, **kwargs):
        resp = self.session.post(
            tl_url,
            headers={
                "accept": "*/*",
                "content-type": "application/octet-stream",
                "referer": referer,
                "x-kpsdk-ct": kpparam["x_kpsdk_ct"],
            },
            data=kpparam["body"],
            **kwargs
        )
        return resp

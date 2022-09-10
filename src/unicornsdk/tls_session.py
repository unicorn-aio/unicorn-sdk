import base64
import typing
from collections import OrderedDict
from typing import Text, MutableMapping, IO, Any, Callable, Container, Mapping

import httpx
import urllib3
from requests import auth as _auth, Response, Request
from requests.adapters import BaseAdapter, HTTPAdapter
from requests.exceptions import InvalidSchema
from requests.utils import resolve_proxies

from unicornsdk.session import Session
from unicornsdk.api.tls import TlsAPI



class TlsSession(Session):

    def __init__(self):
        super(TlsSession, self).__init__()
        self.parrot: str = "Chrome100"
        self.ja3: str = None
        self.http2: bool = True

        # self.adapters = OrderedDict()
        self.tls_adapter = None
        self.tls_api:TlsAPI  = None

    def config_tls(self, parrot=None, ja3=None, http2=None):
        if parrot:
            self.parrot = parrot
        if ja3:
            self.ja3 = ja3
        if http2 is not None:
            self.http2 = bool(http2)

    def request(
            self,
            method,
            url,
            params=None,
            data=None,
            headers=None,
            cookies=None,
            files=None,
            auth=None,
            timeout=None,
            allow_redirects=True,
            proxies=None,
            hooks=None,
            stream=None,
            verify=None,
            cert=None,
            json=None,
    ):
        req = Request(
            method=method.upper(),
            url=url,
            headers=headers,
            files=files,
            data=data or {},
            json=json,
            params=params or {},
            auth=auth,
            cookies=cookies,
            hooks=hooks,
        )
        prep = self.prepare_request(req)

        proxies = proxies or {}

        settings = self.merge_environment_settings(
            prep.url, proxies, stream, verify, cert
        )

        # Send the request.
        send_kwargs = {
            "timeout": timeout,
            "allow_redirects": allow_redirects,
        }
        send_kwargs.update(settings)

        header_order = list(headers.keys() if headers else [])
        send_kwargs["header_order"] = header_order
        resp = self.send(prep, **send_kwargs)

        return resp

    def do_send(self, request, timeout, header_order, **kwargs):
        if not self.tls_api:
            self.tls_api = self._device_session.tls_api(
                parrot=self.parrot, ja3=self.ja3, http2=self.http2,
            )

        kwargs.setdefault("stream", self.stream)
        kwargs.setdefault("verify", self.verify)
        kwargs.setdefault("cert", self.cert)
        if "proxies" not in kwargs:
            kwargs["proxies"] = resolve_proxies(request, self.proxies, self.trust_env)

        # It's possible that users might accidentally send a Request object.
        # Guard against that specific failure case.
        if isinstance(request, Request):
            raise ValueError("You can only send PreparedRequests.")

        # Set up variables needed for resolve_redirects and dispatching of hooks
        allow_redirects = kwargs.pop("allow_redirects", True)
        stream = kwargs.get("stream")
        hooks = request.hooks
        proxies = kwargs.get("proxies")

        if request.url.startswith("https://"):
            proxy_uri = proxies.get("https")
        else:
            proxy_uri = proxies.get("http")

        resp = self.tls_api.request_with_req(request, timeout=timeout, proxy_uri=proxy_uri, header_order=header_order)
        # only handle cookies, not handle redirect
        self.extract_cookies_to_jar(request, resp)
        return resp

    def extract_cookies_to_jar(self, req, resp):
        from httpx import Cookies
        urllib_response = Cookies._CookieCompatResponse(resp)
        urllib_request = Cookies._CookieCompatRequest(resp.request)
        self.cookies.extract_cookies(urllib_response, urllib_request)

        # req = MockRequest(request)
        # # pull out the HTTPMessage with the headers and put it in the mock:
        # res = MockResponse(response._original_response.msg)
        # jar.extract_cookies(res, req)
        aaa = 1

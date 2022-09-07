import base64
import typing
from collections import OrderedDict
from typing import Text, MutableMapping, IO, Any, Callable, Container, Mapping

import httpx
from requests import auth as _auth, Response, Request
from requests.adapters import BaseAdapter
from requests.exceptions import InvalidSchema

from unicornsdk.session import Session
from unicornsdk.api.tls import TlsAPI


class MyTlsAdapter(BaseAdapter):

    def __init__(self, tls_api:TlsAPI):
        super().__init__()
        self.tls_api = tls_api

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None, header_order=None) -> Response:
        resp = Response()
        self.tls_api.request_with_req(request, timeout=timeout, proxy_uri=proxies, header_order=header_order)
        resp.status_code = 200
        return resp





class TlsSession(Session):

    def __init__(self):
        super(TlsSession, self).__init__()
        self.parrot: str = "Chrome100"
        self.ja3: str = None
        self.http2: bool = True

        self.adapters = OrderedDict()
        self.tls_adapter = None

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

    def get_adapter(self, url: str) -> BaseAdapter:
        if not self.tls_adapter:
            self.tls_adapter = MyTlsAdapter(self._device_session.tls_api(
                parrot=self.parrot, ja3=self.ja3, http2=self.http2,
            ))
        if url.lower().startswith("https://"):
            return self.tls_adapter
        elif url.lower().startswith("http://"):
            return self.tls_adapter
        # Nothing matches :-/
        raise InvalidSchema(f"No connection adapters were found for {url!r}")

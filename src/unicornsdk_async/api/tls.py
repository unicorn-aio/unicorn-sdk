import base64
from typing import TYPE_CHECKING, List
import json as _json

import httpx
import requests
from httpx import Cookies, Response

from unicornsdk import exceptions

if TYPE_CHECKING:
    from unicornsdk.api.devicesession import DeviceSession
    from unicornsdk.sdk import UnicornSdk


class TlsAPI:
    CLIENT = httpx.Client()

    def __init__(
            self, sdk: "UnicornSdk", device_session: "DeviceSession",
            proxy_uri=None,
            parrot=None,
            ja3=None,
            http2=True,
            http2Fp=None
    ):
        self.device_session = device_session
        self.sdk = sdk
        self.proxy_uri = proxy_uri
        self.parrot = parrot
        self.ja3 = ja3
        self.http2 = http2
        self.http2Fp = http2Fp

    def construct_forward_request(
            self, request: httpx.Request,
            timeout, header_order: List,
            proxy_uri=None
    ):
        userAgent = request.headers.get("user-agent") or request.headers.get("User-Agent")

        if "Cookie" in request.headers and "Cookie" not in header_order:
            header_order.append("Cookie")
        elif "cookie" in request.headers and "cookie" not in header_order:
            header_order.append("cookie")

        req = {
            "sessionId": self.device_session.session_id,
            "options": {
                "url": str(request.url),
                "method": request.method,
                "headers": dict(request.headers),
                "body": base64.b64encode(request.content).decode(),
                "headerOrder": header_order,
                "userAgent": userAgent
            }
        }
        req["options"]["proxy"] = proxy_uri or self.proxy_uri
        req["options"]["ja3"] = self.ja3
        req["options"]["parrot"] = self.parrot
        req["options"]["timeout"] = timeout
        req["options"]["http2"] = self.http2
        if self.http2Fp:
            req["options"]["http2Fp"] = self.http2Fp
        return req

    def request(self, method, url, *,
                content=None, data=None, files=None, json=None, params=None,
                headers=None, cookies=None,
                timeout=None,
                proxy_uri=None,
                header_order=None,
                **kwargs):
        if not header_order:
            header_order = list(headers.keys()) if headers else []
        request = self.construct_request(
            method, url, content=content, data=data, files=files,
            json=json, params=params, headers=headers, cookies=cookies)
        # 构造请求
        forward_req = self.construct_forward_request(request, timeout, header_order=header_order, proxy_uri=proxy_uri)
        forward_req = _json.dumps(forward_req)
        return self.real_do_forward_request(request, forward_req, timeout)

    def request_with_req(self, req: requests.PreparedRequest, timeout=None, proxy_uri=None, header_order=None):
        headers = dict(req.headers)
        return self.request(
            method=req.method, url=req.url, content=req.body, headers=headers,
            timeout=timeout, proxy_uri=proxy_uri, header_order=header_order
        )

    def real_do_forward_request(self, request, data, timeout):
        client = self.sdk._get_api_client()
        ret = client.post(
            self.sdk.tls_forward_url,
            headers=self.sdk._get_authorization(),
            data=data,
            timeout=timeout,
            verify=False,
            proxies=self.sdk._get_proxys_for_sdk()
        )
        return self.construct_response(ret, request)

    def construct_request(self, method, url,
                          content=None, data=None, files=None, json=None,
                          params=None, headers=None, cookies=None):

        request = TlsAPI.CLIENT.build_request(method, url,
                                              content=content,
                                              data=data,
                                              json=json,
                                              files=files,
                                              params=params,
                                              headers=headers,
                                              cookies=cookies)
        return request

    def construct_response(self, resp: httpx.Response, req: httpx.Request = None):
        if resp.status_code >= 400:
            # 没有请求成功
            errmsg = resp.json()["errmsg"]

            if "Client.Timeout" in errmsg:
                raise requests.exceptions.Timeout()
            else:
                raise exceptions.TlsRequestError(errmsg)

        response = resp.json()["Response"]
        body = base64.b64decode(response["Body"])
        headers = []
        for k, v in response["Headers"].items():
            if k.lower() == "set-cookie":
                for i in v.split("/,/"):
                    headers.append(("Set-Cookie", i))
            else:
                headers.append((k, v))

        fake_resp = httpx.Response(
            status_code=response["Status"],
            headers=headers,
            content=body,
            request=req,
        )
        return fake_resp

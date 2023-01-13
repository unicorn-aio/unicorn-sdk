import base64
import copy
import email.utils
from typing import TYPE_CHECKING, List
import json as _json

import httpx
import requests
from dateutil import parser
from httpx import Cookies, Response
from http.cookiejar import Cookie

if TYPE_CHECKING:
    from unicornsdk.api.devicesession import DeviceSession
    from unicornsdk.sdk import UnicornSdk

from unicornsdk import exceptions

class TlsAPI:
    CLIENT = httpx.Client()

    def __init__(
            self, sdk: "UnicornSdk", device_session: "DeviceSession",
            proxy_uri=None,
            parrot=None,
            ja3=None,
            http2=True,
            http2Fp=None,
            DisableCompression=True,
    ):
        self.device_session = device_session
        self.sdk = sdk
        self.proxy_uri = proxy_uri
        self.parrot = parrot
        self.ja3 = ja3
        self.http2 = http2
        self.http2Fp = http2Fp
        self.DisableCompression = DisableCompression

    def construct_forward_request(
            self, request: httpx.Request,
            timeout, header_order: List,
            proxy_uri=None
    ):
        userAgent = request.headers.get("user-agent") or request.headers.get("User-Agent")

        if "Cookie" in request.headers and "Cookie" not in header_order and "cookie" not in header_order:
            header_order.append("Cookie")

        req = {
            "sessionId": self.device_session.session_id,
            "options": {
                "url": str(request.url),
                "method": request.method,
                # "headers": dict(request.headers),
                "headers": {},
                "body": base64.b64encode(request.content).decode(),
                "headerOrder": header_order,
                "userAgent": userAgent
            }
        }
        encoding = request.headers.encoding
        for i in request.headers.raw:
            k = i[0].decode(encoding)
            v = i[1].decode(encoding)
            req["options"]["headers"][k] = v

        if "host" in request.headers and "host" not in header_order and "Host" not in header_order:
            header_order.insert(0, "host")

        req["options"]["proxy"] = proxy_uri or self.proxy_uri
        req["options"]["ja3"] = self.ja3
        req["options"]["parrot"] = self.parrot
        req["options"]["timeout"] = timeout[0] if hasattr(timeout, '__iter__') else timeout
        req["options"]["http2"] = self.http2
        req["options"]["DisableCompression"] = self.DisableCompression
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
            if "errmsg" in resp.json():
                errmsg = resp.json()["errmsg"]
            elif "detail" in resp.json():
                errmsg = resp.json()["detail"]
            else:
                errmsg = resp.text

            if "Client.Timeout" in errmsg:
                raise exceptions.TimeOutError()
            else:
                raise exceptions.TlsRequestError(f"{resp.status_code}: {errmsg}")

        response = resp.json()["Response"]
        body = base64.b64decode(response["Body"])
        headers = []
        for k, v in response["Headers"].items():
            if k.lower() == "set-cookie":
                for i in v.split("/,/"):
                    headers.append(("Set-Cookie", i))
            else:
                headers.append((k, v))

        req.url = response["URL"]
        fake_resp = httpx.Response(
            status_code=response["Status"],
            headers=headers,
            content=body,
            request=req,
        )
        cookies = []
        # add extra cookie when redirect
        for i in response["Cookies"]:
            cookie = self.server_cookie_to_python_cookie(i)
            cookies.append(cookie)
        return fake_resp, cookies

    def server_cookie_to_python_cookie(self, sc):
        name = sc["name"]
        value = sc["value"]
        if sc["rawExpires"]:
            # expires = parser.isoparse(sc['rawExpires']).timestamp()
            expires = email.utils.parsedate_to_datetime(sc['rawExpires']).timestamp()
        else:
            expires = None
        result = {
            "version": 0,
            "name": name,
            "value": value,
            "port": None,
            "domain": sc["domain"],
            "path": sc["path"],
            "secure": sc["secure"],
            "expires": expires,
            "discard": True,
            "comment": None,
            "comment_url": None,
            "rest": {"HttpOnly": sc['httpOnly']},
            "rfc2109": False,
        }
        result["port_specified"] = bool(result["port"])
        result["domain_specified"] = bool(result["domain"])
        result["domain_initial_dot"] = result["domain"].startswith(".")
        result["path_specified"] = bool(result["path"])
        cookie = Cookie(**result)
        return cookie

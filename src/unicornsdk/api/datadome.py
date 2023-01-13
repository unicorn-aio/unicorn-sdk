import json
import re
from typing import TYPE_CHECKING
import base64
import gzip

from bs4 import BeautifulSoup
from loguru import logger

from unicornsdk.api.baseapi import BaseApi
from unicornsdk import exceptions

if TYPE_CHECKING:
    from unicornsdk.api.devicesession import DeviceSession
    from unicornsdk.sdk import UnicornSdk


class DataDomeAPI(BaseApi):

    def __init__(self, sdk: "UnicornSdk", device_session: "DeviceSession",
                 ddjskey=None,
                 timezoneOffset=None,
                 timezone=None,
                 version="4.5.0",
                 **kwargs
                 ):
        super().__init__(sdk, device_session)
        self.ddjskey = None
        self.ddoptions = None
        self.timezoneOffset = timezoneOffset
        self.timezone = timezone
        self.state = None
        self.version = version
        self.endpoint = None

    def parse_dd_script_tag(self, s):
        """
        !function(a,b,c,d,e,f){a.ddjskey=e;a.ddoptions=f||null;var m=b.createElement(c),n=b.getElementsByTagName(c)[0];m.async=1,m.src=d,n.parentNode.insertBefore(m,n)}(window,document,"script","https://d.digital.hermes/tags.js","2211F522B61E269B869FA6EAFFB5E1",{endpoint: 'https://d.digital.hermes/js/', ajaxListenerPath: 'hermes.c'});
        """
        params = s.strip().split('"script"')[1].strip("\",;)").split(",")
        ddoptions_str = params[2] + "," + params[3]
        ddoptions = {}
        for i in ddoptions_str.strip("{}").split(","):
            sep = i.find(":")
            k = i[:sep]
            v = i[sep + 2:].strip("\"'")
            ddoptions[k] = v

        ret = {
            "tags_url": params[0].strip("\""),
            "ddjskey": params[1].strip("\""),
            "ddoptions": ddoptions
        }
        return ret

    def parse_html(self, html_content: str):
        bs = BeautifulSoup(html_content, "lxml")
        for i in bs.find_all("script"):
            if i.text.find("ddoption") != -1:
                conf = self.parse_dd_script_tag(i.text.strip())
                self.tags_url = conf["tags_url"]
                self.ddjskey = conf["ddjskey"]
                self.ddoptions = conf["ddoptions"]
                self.endpoint = self.ddoptions["endpoint"]
                return conf
        return None

    def gen_payload(self, cur_url, timezoneOffset, timezone, dd_cookie, ddoptions=None, ddjskey=None, le=False):
        param = {
            "cur_url": str(cur_url),
            "timezoneOffset": timezoneOffset,
            "timezone": timezone,
            "dd_cookie": dd_cookie,
            "ddoptions": ddoptions or self.ddoptions,
            "ddjskey": ddjskey or self.ddjskey,
        }
        if le and not self.state:
            raise exceptions.ParamsError("le must call after ch!")

        resp = self.post(
            url=self._sdk.api_url + "/api/datadome/payload/",
            json=param,
        )
        resp = resp.json()
        self.state = resp["state"]
        return resp["payload"]

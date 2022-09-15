from datetime import datetime

from dateutil import parser


def parse_from_iso8601_to_local(dt_str):
    if not dt_str:
        return None
    return parser.isoparse(dt_str).astimezone()

def now_time_s():
    return int(datetime.now().timestamp())

def now_time_ms():
    return int(datetime.now().timestamp() * 1000)

def now_time_str():
    return datetime.now().strftime("%Y%m%d-%H%M%S")



def infer_platform(userAgent):
    if userAgent.find("Windows NT") != -1:
        platform = "WINDOWS"
    elif userAgent.find("Android") != -1:
        platform = "ANDROID"
        # platform_type = PlatFormType.MOBILE
    elif userAgent.find("iPhone") != -1:
        platform = "IOS"
        # platform_type = PlatFormType.MOBILE
    elif userAgent.find("Mac OS X") != -1:
        platform = "OSX"
    return platform


def accept_language_to_languages(accept_language):
    # en,zh-CN;q=0.9,zh-HK;q=0.8,zh;q=0.7,ja;q=0.6
    langs = []
    bases = set()

    for i in accept_language.split(","):
        lang = i.split(";")[0]
        if lang.find("-") != -1:
            base = lang.split("-")[0]
            bases.add(base)
        if lang not in bases:
            langs.append(lang)
    return langs

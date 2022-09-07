from enum import Enum

VERSION = "0.0.4"

import urllib3
urllib3.disable_warnings()

class PlatForm(str, Enum):
    WINDOWS = "WINDOWS"
    ANDROID = "ANDROID"
    IOS = "IOS"
    OSX = "OSX"



from .sdk import UnicornSdk
from .session import Session
from .tls_session import TlsSession

from unicornsdk.api.devicesession import DeviceSession




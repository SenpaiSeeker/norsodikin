from types import SimpleNamespace

from .addUser import SSHUserManager
from .argument import Argument
from .bing import ImageGenerator
from .button import Button
from .colorize import AnsiColors
from .database import DataBase
from .encrypt import AsciiManager, CipherHandler
from .gemini import ChatbotGemini
from .gradient import Gradient
from .logger import LoggerHandler
from .payment import PaymentMidtrans, PaymentTripay, VioletMediaPayClient
from .storekey import KeyManager
from .ymlreder import YamlHandler

__version__ = "1.0.4"
__author__ = "@NorSodikin"


class NsDev:
    def __init__(self, client):
        self._client = client

        self.ai = SimpleNamespace(
            bing=ImageGenerator,
            gemini=ChatbotGemini,
        )

        self.telegram = SimpleNamespace(
            arg=Argument(),
            button=Button(),
        )

        self.data = SimpleNamespace(
            db=DataBase,
            key=KeyManager,
            yaml=YamlHandler(),
        )

        self.utils = SimpleNamespace(
            color=AnsiColors(),
            grad=Gradient(),
            log=LoggerHandler(),
        )

        self.server = SimpleNamespace(
            user=SSHUserManager,
        )

        self.code = SimpleNamespace(
            Cipher=CipherHandler,
            Ascii=AsciiManager,
        )

        self.payment = SimpleNamespace(
            Midtrans=PaymentMidtrans,
            Tripay=PaymentTripay,
            Violet=VioletMediaPayClient,
        )


@property
def ns(self) -> NsDev:
    if not hasattr(self, "_nsdev_instance"):
        self._nsdev_instance = NsDev(self)
    return self._nsdev_instance


try:
    from pyrogram import Client

    Client.ns = ns
except Exception:
    pass

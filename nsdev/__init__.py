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
from .listen import *
from .logger import LoggerHandler
from .payment import PaymentMidtrans, PaymentTripay, VioletMediaPayClient
from .storekey import KeyManager
from .ymlreder import YamlHandler

__version__ = "0.9.8.3"
__author__ = "@NorSodikin"


class NsDev:
    def __init__(self, client):
        self._client = client

        self.arg = Argument()
        self.button = Button()
        self.color = AnsiColors()
        self.grad = Gradient()
        self.yaml = YamlHandler()

        self.bing = ImageGenerator
        self.db = DataBase
        self.gemini = ChatbotGemini
        self.log = LoggerHandler
        self.key = KeyManager
        self.user = SSHUserManager

        self.code = SimpleNamespace(Cipher=CipherHandler, Ascii=AsciiManager)
        self.payment = SimpleNamespace(Midtrans=PaymentMidtrans, Tripay=PaymentTripay, Violet=VioletMediaPayClient)


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

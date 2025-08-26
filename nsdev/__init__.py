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
from .huggingface import HuggingFaceGenerator
from .logger import LoggerHandler
from .payment import PaymentMidtrans, PaymentTripay, VioletMediaPayClient
from .storekey import KeyManager
from .ymlreder import YamlHandler
from .monitor import ServerMonitor
from .tts import TextToSpeech
from .web_summarizer import WebSummarizer
from .progress import TelegramProgressBar
from .formatter import TextFormatter
from .translate import Translator
from .qrcode import QrCodeGenerator
from .actions import TelegramActions
from .shell import ShellExecutor
from .url import UrlUtils

__version__ = "1.2.0"
__author__ = "@NorSodikin"

class NsDev:
    def __init__(self, client):
        self._client = client
        self.ai = SimpleNamespace(
            bing=ImageGenerator,
            gemini=ChatbotGemini,
            hf=HuggingFaceGenerator,
            tts=TextToSpeech,
            web=WebSummarizer,
            translate=Translator,
            qrcode=QrCodeGenerator,
        )
        self.telegram = SimpleNamespace(
            arg=Argument(self._client),
            button=Button(),
            formatter=TextFormatter,
            actions=TelegramActions(self._client),
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
            progress=TelegramProgressBar,
            shell=ShellExecutor(),
            url=UrlUtils(),
        )
        self.server = SimpleNamespace(
            user=SSHUserManager,
            monitor=ServerMonitor(),
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

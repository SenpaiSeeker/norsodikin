from types import SimpleNamespace

from .ai.bing import ImageGenerator
from .ai.gemini import ChatbotGemini
from .ai.huggingface import HuggingFaceGenerator
from .ai.local import OllamaClient
from .ai.qrcode import QrCodeGenerator
from .ai.stt import SpeechToText
from .ai.translate import Translator
from .ai.tts import TextToSpeech
from .ai.vision import VisionAnalyzer
from .ai.web_summarizer import WebSummarizer
from .code.encrypt import AsciiManager, CipherHandler
from .data.database import DataBase
from .data.storekey import KeyManager
from .data.ymlreder import YamlHandler
from .payment.payment import PaymentMidtrans, PaymentTripay, VioletMediaPayClient
from .server.addUser import SSHUserManager
from .server.monitor import ServerMonitor
from .server.process import ProcessManager
from .telegram.actions import TelegramActions
from .telegram.argument import Argument
from .telegram.button import Button
from .telegram.formatter import TextFormatter
from .telegram.videofx import VideoFX
from .utils.colorize import AnsiColors
from .utils.downloader import MediaDownloader
from .utils.gradient import Gradient
from .utils.logger import LoggerHandler
from .utils.progress import TelegramProgressBar
from .utils.shell import ShellExecutor
from .utils.url import UrlUtils

__version__ = "1.6.4"
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
            vision=VisionAnalyzer,
            stt=SpeechToText,
            local=OllamaClient,
        )
        self.telegram = SimpleNamespace(
            arg=Argument(self._client),
            button=Button(),
            formatter=TextFormatter,
            actions=TelegramActions(self._client),
            videofx=VideoFX(),
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
            downloader=MediaDownloader(cookies_file_path="cookies.txt"),
        )
        self.server = SimpleNamespace(
            user=SSHUserManager,
            monitor=ServerMonitor(),
            process=ProcessManager(),
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

from types import SimpleNamespace

from .telegram.actions import TelegramActions
from .server.addUser import SSHUserManager
from .telegram.argument import Argument
from .ai.bing import ImageGenerator
from .telegram.button import Button
from .utils.colorize import AnsiColors
from .data.database import DataBase
from .utils.downloader import MediaDownloader
from .code.encrypt import AsciiManager, CipherHandler
from .telegram.formatter import TextFormatter
from .ai.gemini import ChatbotGemini
from .utils.gradient import Gradient
from .ai.huggingface import HuggingFaceGenerator
from .ai.local import OllamaClient
from .utils.logger import LoggerHandler
from .server.monitor import ServerMonitor
from .payment.payment import PaymentMidtrans, PaymentTripay, VioletMediaPayClient
from .server.process import ProcessManager
from .utils.progress import TelegramProgressBar
from .ai.qrcode import QrCodeGenerator
from .utils.shell import ShellExecutor
from .data.storekey import KeyManager
from .ai.stt import SpeechToText
from .ai.translate import Translator
from .ai.tts import TextToSpeech
from .utils.url import UrlUtils
from .telegram.videofx import VideoFX
from .ai.vision import VisionAnalyzer
from .ai.web_summarizer import WebSummarizer
from .data.ymlreder import YamlHandler

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

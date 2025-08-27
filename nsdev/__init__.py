from types import SimpleNamespace

from .actions import TelegramActions
from .addUser import SSHUserManager
from .argument import Argument
from .bing import ImageGenerator
from .button import Button
from .colorize import AnsiColors
from .database import DataBase
from .downloader import MediaDownloader
from .encrypt import AsciiManager, CipherHandler
from .formatter import TextFormatter
from .gemini import ChatbotGemini
from .gradient import Gradient
from .huggingface import HuggingFaceGenerator
from .local import OllamaClient
from .logger import LoggerHandler
from .monitor import ServerMonitor
from .payment import PaymentMidtrans, PaymentTripay, VioletMediaPayClient
from .process import ProcessManager
from .progress import TelegramProgressBar
from .qrcode import QrCodeGenerator
from .shell import ShellExecutor
from .storekey import KeyManager
from .stt import SpeechToText
from .translate import Translator
from .tts import TextToSpeech
from .url import UrlUtils
from .videofx import VideoFX
from .vision import VisionAnalyzer
from .web_summarizer import WebSummarizer
from .ymlreder import YamlHandler

__version__ = "1.5.9"
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

from types import SimpleNamespace

from .ai.bing import ImageGenerator
from .ai.gemini import ChatbotGemini
from .ai.huggingface import HuggingFaceGenerator
from .ai.local import OllamaClient
from .ai.ocr import OCR
from .ai.qrcode import QrCodeGenerator
from .ai.search import WebSearch
from .ai.stt import SpeechToText
from .ai.translate import Translator
from .ai.tts import TextToSpeech
from .ai.upscaler import ImageUpscaler
from .ai.vision import VisionAnalyzer
from .ai.voicecloning import VoiceCloner
from .ai.web_summarizer import WebSummarizer
from .analytics.chat import ChatAnalyzer
from .analytics.manager import AnalyticsManager
from .auth.manager import AuthManager
from .code.encrypt import AsciiManager, CipherHandler
from .data.database import DataBase
from .data.storekey import KeyManager
from .data.ymlreder import YamlHandler
from .payment.payment import (
    PaymentCashify,
    PaymentMidtrans,
    PaymentTripay,
    SaweriaApi,
    VioletMediaPayClient,
)
from .schedule.manager import Scheduler
from .server.addUser import SSHUserManager
from .server.monitor import ServerMonitor
from .server.process import ProcessManager
from .server.speedtest import SpeedtestRunner
from .telegram.actions import TelegramActions
from .telegram.argument import Argument
from .telegram.button import Button
from .telegram.copier import MessageCopier
from .telegram.errors import ErrorHandler
from .telegram.formatter import TextFormatter
from .telegram.story import StoryDownloader
from .telegram.videofx import VideoFX
from .tempmail.manager import TempMailManager
from .utils.audiofx import AudioFX
from .utils.cache import memoize
from .utils.carbon import CarbonClient
from .utils.colorize import AnsiColors
from .utils.downloader import MediaDownloader
from .utils.faker import FakeInfoGenerator
from .utils.files import FileManager
from .utils.fonts import FontChanger
from .utils.github import GitHubInfo
from .utils.gofile import GoFileUploader
from .utils.gradient import Gradient
from .utils.image import ImageManipulator
from .utils.logger import CustomLogHandler, LoggerHandler
from .utils.lookup import TMDbClient
from .utils.mediainfo import MediaInspector
from .utils.osint import OsintTools
from .utils.paste import PasteClient
from .utils.pinterest import PinterestAPI
from .utils.progress import TelegramProgressBar
from .utils.ratelimit import RateLimiter
from .utils.shell import ShellExecutor
from .utils.splitter import AudioSplitter
from .utils.url import UrlUtils
from .utils.weather import WeatherWttr
from .utils.wikipedia import WikipediaSearch

__version__ = "2.3.4"
__author__ = "@NorSodikin"


class NsDev:
    def __init__(self, client):
        self._client = client
        self.ai = SimpleNamespace(
            bing=ImageGenerator,
            gemini=ChatbotGemini,
            hf=HuggingFaceGenerator,
            local=OllamaClient,
            ocr=OCR,
            qrcode=QrCodeGenerator(),
            search=WebSearch,
            stt=SpeechToText,
            translate=Translator,
            tts=TextToSpeech,
            upscaler=ImageUpscaler,
            vision=VisionAnalyzer,
            voicecloning=VoiceCloner,
            web=WebSummarizer,
        )
        self.analytics = SimpleNamespace(
            manager=AnalyticsManager,
            chat=ChatAnalyzer,
        )
        self.auth = AuthManager
        self.code = SimpleNamespace(
            Ascii=AsciiManager,
            Cipher=CipherHandler,
        )
        self.data = SimpleNamespace(
            db=DataBase,
            key=KeyManager,
            yaml=YamlHandler(),
        )
        self.payment = SimpleNamespace(
            Cashify=PaymentCashify,
            Midtrans=PaymentMidtrans,
            Saweria=SaweriaApi,
            Tripay=PaymentTripay,
            Violet=VioletMediaPayClient,
        )
        self.schedule = Scheduler()
        self.server = SimpleNamespace(
            monitor=ServerMonitor(),
            process=ProcessManager(),
            speedtest=SpeedtestRunner(),
            user=SSHUserManager,
        )
        self.telegram = SimpleNamespace(
            actions=TelegramActions(self._client),
            arg=Argument(self._client),
            button=Button(),
            copier=MessageCopier(self._client),
            errors=ErrorHandler(self._client),
            formatter=TextFormatter,
            story=StoryDownloader(self._client),
            videofx=VideoFX(),
        )
        self.tempmail = TempMailManager()
        self.utils = SimpleNamespace(
            audiofx=AudioFX(),
            cache=memoize,
            carbon=CarbonClient,
            color=AnsiColors(),
            downloader=MediaDownloader,
            faker=FakeInfoGenerator(),
            files=FileManager(),
            font=FontChanger(),
            github=GitHubInfo,
            gofile=GoFileUploader(),
            grad=Gradient(),
            image=ImageManipulator(),
            log=LoggerHandler,
            lookup=TMDbClient,
            mediainfo=MediaInspector(),
            osint=OsintTools,
            paste=PasteClient,
            pinterest=PinterestAPI,
            progress=TelegramProgressBar,
            ratelimit=RateLimiter(self._client),
            shell=ShellExecutor(),
            splitter=AudioSplitter,
            url=UrlUtils(),
            weather=WeatherWttr,
            wikipedia=WikipediaSearch,
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

from types import SimpleNamespace

from .ai.bing import ImageGenerator
from .ai.gemini import ChatbotGemini
from .ai.huggingface import HuggingFaceGenerator
from .ai.local import OllamaClient
from .ai.qrcode import QrCodeGenerator
from .ai.search import WebSearch
from .ai.stt import SpeechToText
from .ai.translate import Translator
from .ai.tts import TextToSpeech
from .ai.vision import VisionAnalyzer
from .ai.web_summarizer import WebSummarizer
from .analytics.chat import ChatAnalyzer
from .analytics.manager import AnalyticsManager
from .auth.manager import AuthManager
from .code.encrypt import AsciiManager, CipherHandler
from .data.database import DataBase
from .data.storekey import KeyManager
from .data.ymlreder import YamlHandler
from .payment.payment import PaymentMidtrans, PaymentTripay, VioletMediaPayClient
from .schedule.manager import Scheduler
from .server.addUser import SSHUserManager
from .server.monitor import ServerMonitor
from .server.process import ProcessManager
from .telegram.actions import TelegramActions
from .telegram.argument import Argument
from .telegram.button import Button
from .telegram.copier import MessageCopier
from .telegram.errors import ErrorHandler
from .telegram.formatter import TextFormatter
from .telegram.story import StoryDownloader
from .telegram.videofx import VideoFX
from .utils.cache import memoize
from .utils.carbon import CarbonClient
from .utils.colorize import AnsiColors
from .utils.downloader import MediaDownloader
from .utils.files import FileManager
from .utils.github import GitHubInfo
from .utils.gradient import Gradient
from .utils.image import ImageManipulator
from .utils.logger import LoggerHandler
from .utils.lookup import TMDbClient
from .utils.osint import OsintTools
from .utils.paste import PasteClient
from .utils.progress import TelegramProgressBar
from .utils.ratelimit import RateLimiter
from .utils.shell import ShellExecutor
from .utils.url import UrlUtils
from .utils.wikipedia import WikipediaSearch

__version__ = "1.9.0"
__author__ = "@NorSodikin"


class NsDev:
    def __init__(self, client):
        self._client = client
        self.ai = SimpleNamespace(
            bing=ImageGenerator,
            gemini=ChatbotGemini,
            hf=HuggingFaceGenerator,
            local=OllamaClient,
            qrcode=QrCodeGenerator,
            search=WebSearch,
            stt=SpeechToText,
            translate=Translator,
            tts=TextToSpeech,
            vision=VisionAnalyzer,
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
            Midtrans=PaymentMidtrans,
            Tripay=PaymentTripay,
            Violet=VioletMediaPayClient,
        )
        self.schedule = Scheduler()
        self.server = SimpleNamespace(
            monitor=ServerMonitor(),
            process=ProcessManager(),
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
        self.utils = SimpleNamespace(
            cache=memoize,
            carbon=CarbonClient,
            color=AnsiColors(),
            downloader=MediaDownloader,
            files=FileManager(),
            github=GitHubInfo,
            grad=Gradient(),
            image=ImageManipulator(),
            log=LoggerHandler,
            lookup=TMDbClient,
            osint=OsintTools,
            paste=PasteClient,
            progress=TelegramProgressBar,
            ratelimit=RateLimiter(self._client),
            shell=ShellExecutor(),
            url=UrlUtils(),
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

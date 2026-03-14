from types import SimpleNamespace

from .ai import (
    OCR,
    ChatbotGemini,
    HuggingFaceGenerator,
    ImageGenerator,
    ImageUpscaler,
    QrCodeGenerator,
    SpeechToText,
    TextToSpeech,
    Translator,
    VisionAnalyzer,
    VoiceCloner,
    WebSearch,
    WebSummarizer,
)
from .analytics import AnalyticsManager, ChatAnalyzer
from .auth import AuthManager
from .code import AsciiManager, CipherHandler, CodeRenderer
from .data import DataBase, KeyManager, YamlHandler
from .game import GameEngine
from .listeners import (
    ListenerCanceled,
    ListenerManager,
    ListenerStopped,
    ListenerTimeout,
)
from .payment import (
    PaymentCashify,
    PaymentMidtrans,
    PaymentTripay,
    SaweriaApi,
    SaweriaScraper,
    VioletMediaPayClient,
)
from .pinterest import Pinterest
from .schedule import Scheduler
from .server import (
    FirewallManager,
    ProcessManager,
    RemoteExecutor,
    ServerMonitor,
    SpeedtestRunner,
    SSHUserManager,
)
from .telegram import (
    Argument,
    Button,
    CalendarUI,
    ErrorHandler,
    MessageCopier,
    StoryDownloader,
    TelegramActions,
    TextFormatter,
    ThemeGenerator,
    VideoFX,
)
from .tempmail import TempMailManager
from .utils import (
    AnsiColors,
    AudioFX,
    AudioSplitter,
    AudioVisualizer,
    CarbonClient,
    CustomLogHandler,
    DeviceMockup,
    FakeInfoGenerator,
    FileManager,
    FontChanger,
    GitHubInfo,
    GoFileUploader,
    Gradient,
    ImageInpainter,
    ImageManipulator,
    LoggerHandler,
    LyricsFinder,
    MediaDownloader,
    MediaInspector,
    OsintTools,
    PasteClient,
    RateLimiter,
    ShazamHelper,
    ShellExecutor,
    TelegramProgressBar,
    TMDbClient,
    UrlUtils,
    WeatherWttr,
    WebArchiver,
    WebAutomation,
    WikipediaSearch,
    memoize,
)

__version__ = "2026.03.108"
__author__ = "NorSodikin.t.me"


class NsDev:
    def __init__(self, client):
        self._client = client
        self.ai = SimpleNamespace(
            bing=ImageGenerator,
            gemini=ChatbotGemini,
            hf=HuggingFaceGenerator,
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
            Render=CodeRenderer,
        )
        self.data = SimpleNamespace(
            db=DataBase,
            key=KeyManager,
            yaml=YamlHandler(),
        )
        self.game = SimpleNamespace(
            engine=GameEngine(),
        )
        self.listeners = ListenerManager(self._client)
        self.payment = SimpleNamespace(
            Cashify=PaymentCashify,
            Midtrans=PaymentMidtrans,
            Saweria=SaweriaApi,
            SaweriaScraper=SaweriaScraper,
            Tripay=PaymentTripay,
            Violet=VioletMediaPayClient,
        )
        self.pinterest = Pinterest()
        self.schedule = Scheduler()
        self.server = SimpleNamespace(
            monitor=ServerMonitor(),
            process=ProcessManager(),
            speedtest=SpeedtestRunner(),
            user=SSHUserManager,
            remote=RemoteExecutor(),
            firewall=FirewallManager(),
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
            calendar=CalendarUI(),
            theme=ThemeGenerator(),
        )
        self.tempmail = TempMailManager()
        self.utils = SimpleNamespace(
            archiver=WebArchiver(),
            audiofx=AudioFX(),
            visualizer=AudioVisualizer(),
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
            inpainter=ImageInpainter(),
            mockup=DeviceMockup(),
            log=LoggerHandler,
            lookup=TMDbClient,
            mediainfo=MediaInspector(),
            osint=OsintTools,
            paste=PasteClient,
            progress=TelegramProgressBar,
            ratelimit=RateLimiter(self._client),
            shell=ShellExecutor(),
            splitter=AudioSplitter,
            url=UrlUtils(),
            weather=WeatherWttr,
            web=WebAutomation(),
            wikipedia=WikipediaSearch,
            shazam=ShazamHelper(),
            lyrics=LyricsFinder(),
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

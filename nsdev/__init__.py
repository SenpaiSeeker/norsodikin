import pyrogram
import functools
from pyrogram import Client

if not hasattr(Client, "_norsodikin_patched"):

    from .addUser import SSHUserManager
    from .argument import Argument
    from .bing import ImageGenerator
    from .button import Button
    from .colorize import AnsiColors
    from .database import DataBase
    from .encrypt import CipherHandler
    from .gemini import ChatbotGemini
    from .gradient import Gradient
    from .logger import LoggerHandler
    from .payment import PaymentMidtrans, PaymentTripay, VioletMediaPayClient
    from .storekey import KeyManager
    from .yaml_reader import YAMLReader

    __version__ = "1.0.0"
  
    class NsDevAccessor:
        def __init__(self, client: Client):
            self._client = client
            self.addUser: SSHUserManager = SSHUserManager(client)
            self.argument: Argument = Argument(client)
            
            self.bing = ImageGenerator
            self.button = Button()
            self.colorize = AnsiColors()
            self.database = DataBase
            self.encrypt = CipherHandler
            self.gemini = ChatbotGemini
            self.gradient = Gradient()
            self.logger = LoggerHandler()
            self.payment_midtrans = PaymentMidtrans
            self.payment_tripay = PaymentTripay
            self.payment_violet = VioletMediaPayClient
            self.storekey = KeyManager()
            self.yaml_reader = YAMLReader()

    _old_init = Client.__init__

    @functools.wraps(_old_init)
    def _new_init(self, *args, **kwargs):
        _old_init(self, *args, **kwargs)
        self.ns = NsDevAccessor(self)

    Client.__init__ = _new_init
    
    Client._norsodikin_patched = True

    __all__ = [
        "SSHUserManager", "Argument", "ImageGenerator", "Button",
        "AnsiColors", "DataBase", "CipherHandler", "ChatbotGemini",
        "Gradient", "LoggerHandler", "PaymentMidtrans", "PaymentTripay",
        "VioletMediaPayClient", "KeyManager", "YAMLReader"
    ]

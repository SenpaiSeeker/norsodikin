from types import SimpleNamespace

import pyrogram

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

__version__ = "0.8.0"
__author__ = "@NorSodikin"


class NsDev:
    """
    Kelas 'jembatan' yang akan diinjeksikan ke dalam objek client Pyrogram.
    Ini bertindak sebagai namespace utama (client.ns) yang menyediakan akses
    ke semua fungsionalitas pustaka norsodikin.
    """

    def __init__(self, client: "pyrogram.Client"):
        self._client = client

        # --------------------------------------------------------------------------
        # A. Helper/Utilitas yang Stateless (Bisa langsung diinisialisasi)
        # Aksesnya lebih singkat dan praktis, mis: client.ns.log.info(...)
        # --------------------------------------------------------------------------
        self.arg = Argument()
        self.button = Button()
        self.color = AnsiColors()
        self.grad = Gradient()
        self.log = LoggerHandler()
        self.yaml = YamlHandler()

        # --------------------------------------------------------------------------
        # B. Kelas Stateful/Perlu Konfigurasi (Mengekspos kelasnya langsung)
        # Pengguna perlu membuat instance sendiri dengan konfigurasinya.
        # mis: db = client.ns.db(storage_type="local", file_name="my_db")
        # --------------------------------------------------------------------------
        self.db = DataBase
        self.user = SSHUserManager
        self.bing = ImageGenerator
        self.gemini = ChatbotGemini
        self.key = KeyManager

        # --------------------------------------------------------------------------
        # C. Pengelompokan Kelas menggunakan SimpleNamespace
        # Sesuai permintaan, untuk file dengan lebih dari satu kelas.
        # mis: cipher = client.ns.encrypt.CipherHandler(key=123)
        # mis: payment_handler = client.ns.payment.Midtrans(...)
        # --------------------------------------------------------------------------
        self.encrypt = SimpleNamespace(CipherHandler=CipherHandler, AsciiManager=AsciiManager)

        self.payment = SimpleNamespace(
            Midtrans=PaymentMidtrans, Tripay=PaymentTripay, VioletMediaPay=VioletMediaPayClient
        )


# ----------------------------------------------------------------------------------
# D. "Monkey Patching" ke dalam Pyrogram Client
# Ini adalah bagian inti yang membuat `client.ns` bisa digunakan.
# Kita membuat sebuah property 'ns' di kelas pyrogram.Client.
# ----------------------------------------------------------------------------------
@property
def ns(self: "pyrogram.Client") -> NsDev:
    """
    Property untuk mengakses fungsionalitas NsDev dari instance client.
    Instance NsDev akan dibuat sekali dan di-cache dalam `_nsdev_instance`
    untuk efisiensi.
    """
    if not hasattr(self, "_nsdev_instance"):
        self._nsdev_instance = NsDev(self)
    return self._nsdev_instance


pyrogram.Client.ns = ns
__all__ = ["NsDev"]

class PaymentMidtrans:
    def __init__(self, server_key, client_key, callback_url="https://SenpaiSeeker.github.io/payment", is_production=True):
        self.midtransclient = __import__("midtransclient")
        self.snap = self.midtransclient.Snap(
            is_production=is_production,
            server_key=server_key,
            client_key=client_key,
        )
        self.callback_url = callback_url

    def createPayment(self, order_id, gross_amount):
        try:
            param = {
                "transaction_details": {
                    "order_id": order_id,
                    "gross_amount": gross_amount,
                },
                "enabled_payments": ["other_qris"],
                "callbacks": {
                    "finish": self.callback_url,
                },
            }
            return self.snap.create_transaction(param)
        except Exception as e:
            return f"Error saat membuat transaksi: {e}"

    def checkTansactionStatus(self, order_id):
        try:
            return self.snap.transactions.status(order_id)
        except Exception as e:
            return f"Error saat mengecek status transaksi: {e}"


class PaymentTripay:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://tripay.co.id/api"

        self.requests = __import__("requests")
        self.convert = __import__("nsdev").YamlHandler()

    def createPayment(self, method, amount, order_id, customer_name):
        url = f"{self.base_url}/transaction/create"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"method": method, "merchant_ref": order_id, "amount": amount, "customer_name": customer_name}

        response = self.requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Error creating payment: {response.json().get('message')}")

        return self.convert._convertToNamespace(response.json())

    def checkPayment(self, reference):
        url = f"{self.base_url}/transaction/detail"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"reference": reference}

        response = self.requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Error checking payment: {response.json().get('message')}")

        return self.convert._convertToNamespace(response.json())


class VioletMediaPayClient:
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        live: bool = False,
    ):
        self.httpx = __import__("httpx")
        self.hmac = __import__("hmac")
        self.hashlib = __import__("hashlib")
        self.time = __import__("time")
        self.uuid = __import__("uuid")
        self.faker = __import__("faker").Faker("id_ID")
        self.convert = __import__("nsdev").YamlHandler()

        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://violetmediapay.com/api/live" if live else "https://violetmediapay.com/api/sanbox"

    def _generate_signature(self, ref_kode: str, amount: str) -> str:
        message = f"{ref_kode}{self.api_key}{amount}"
        signature = self.hmac.new(self.secret_key.encode(), message.encode(), self.hashlib.sha256).hexdigest()
        return signature

    async def create_payment(
        self,
        channel_payment: str = "QRIS",
        amount: str = "1500",
        produk: str = "payment_bot",
        url_redirect: str = "https://domainanda.com/redirect",
        url_callback: str = "https://domainanda.com/callback",
    ):
        url = f"{self.base_url}/create"

        ref_kode = str(self.uuid.uuid4().hex)
        signature = self._generate_signature(ref_kode, amount)
        expired_time = int(self.time.time()) + 24 * 60 * 60

        cus_nama = self.faker.name()
        cus_email = self.faker.email()
        cus_phone = self.faker.phone_number()

        payload = {
            "api_key": self.api_key,
            "secret_key": self.secret_key,
            "channel_payment": channel_payment,
            "ref_kode": ref_kode,
            "nominal": amount,
            "cus_nama": cus_nama,
            "cus_email": cus_email,
            "cus_phone": cus_phone,
            "produk": produk,
            "url_redirect": url_redirect,
            "url_callback": url_callback,
            "expired_time": expired_time,
            "signature": signature,
        }

        async with self.httpx.AsyncClient(verify=False) as client:
            response = await client.post(url, data=payload)
            return self.convert._convertToNamespace(
                {
                    "api_response": response.json(),
                    "ref_kode": ref_kode,
                    "customer": {
                        "nama": cus_nama,
                        "email": cus_email,
                        "phone": cus_phone,
                    },
                }
            )

    async def check_transaction(self, ref: str, ref_id: str):
        url = f"{self.base_url}/transactions"

        payload = {
            "api_key": self.api_key,
            "secret_key": self.secret_key,
            "ref": ref,
            "ref_id": ref_id,
        }

        async with self.httpx.AsyncClient(verify=False) as client:
            response = await client.post(url, data=payload)
            return self.convert._convertToNamespace(response.json())

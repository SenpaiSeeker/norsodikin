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

    def createPayment(self, method, amount, order_id, customer_name):
        url = f"{self.base_url}/transaction/create"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"method": method, "merchant_ref": order_id, "amount": amount, "customer_name": customer_name}

        response = self.requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Error creating payment: {response.json().get('message')}")

        return response.json()

    def checkPayment(self, reference):
        url = f"{self.base_url}/transaction/detail"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"reference": reference}

        response = self.requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Error checking payment: {response.json().get('message')}")

        return response.json()

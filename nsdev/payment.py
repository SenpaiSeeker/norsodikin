class PaymentMidtrans:
    def __init__(self, server_key, client_key, is_production=True):
        self.midtransclient = __import__("midtransclient")
        self.snap = self.midtransclient.Snap(
            is_production=is_production,
            server_key=server_key,
            client_key=client_key,
        )

    def createPayment(self, order_id, gross_amount):
        try:
            param = {
                "transaction_details": {
                    "order_id": order_id,
                    "gross_amount": gross_amount,
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

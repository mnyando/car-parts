import base64
import datetime
import requests
import os

class MpesaClient:
    """Minimal M-Pesa (Daraja) client for OAuth and STK Push.

    This client supports sandbox and production. It expects the following env/config:
    - consumer_key, consumer_secret (required)
    - env: 'sandbox' or 'production'
    - shortcode and passkey for STK Push (required to actually push)
    """

    def __init__(self, consumer_key: str, consumer_secret: str, env: str = 'sandbox', shortcode: str = None, passkey: str = None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.env = env
        self.shortcode = shortcode
        self.passkey = passkey
        self.token = None
        # If keys are not provided, operate in disabled mode and raise on operations
        self.disabled = not (consumer_key and consumer_secret)

    def _base_url(self):
        if self.env == 'production':
            return 'https://api.safaricom.co.ke'
        return 'https://sandbox.safaricom.co.ke'

    def _get_oauth_token(self):
        if self.disabled:
            raise RuntimeError('M-Pesa client not configured (consumer key/secret missing)')
        url = f"{self._base_url()}/oauth/v1/generate?grant_type=client_credentials"
        auth = (self.consumer_key, self.consumer_secret)
        r = requests.get(url, auth=auth)
        r.raise_for_status()
        data = r.json()
        self.token = data['access_token']
        return self.token

    def stk_push(self, phone_number: str, amount: float, account_reference: str, transaction_desc: str = 'Payment'):
        """Send STK Push (Lipa na M-PESA Online). Returns the API response as dict.

        Note: shortcode and passkey must be configured. If not set, this method will raise an informative error.
        """
        if self.disabled:
            raise RuntimeError('M-Pesa not configured. Set MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET to enable payments.')

        if not self.shortcode or not self.passkey:
            raise RuntimeError('MPESA_SHORTCODE and MPESA_PASSKEY must be configured to perform STK Push')

        if not self.token:
            self._get_oauth_token()

        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()

        url = f"{self._base_url()}/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": os.getenv('MPESA_CALLBACK_URL', 'https://example.com/mpesa/callback'),
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code >= 400:
            print(f"Safaricom STK Push failed with status {r.status_code}: {r.text}", flush=True)
        r.raise_for_status()
        return r.json()

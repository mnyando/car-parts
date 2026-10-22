import base64
import datetime
import time
import requests
import os

# Seconds to wait for Safaricom before giving up on a request
REQUEST_TIMEOUT = 30


class MpesaError(RuntimeError):
    """Raised when M-Pesa is misconfigured or Safaricom rejects a request."""


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
        self.token_expires_at = 0
        # If keys are not provided, operate in disabled mode and raise on operations
        self.disabled = not (consumer_key and consumer_secret)

    def _base_url(self):
        if self.env == 'production':
            return 'https://api.safaricom.co.ke'
        return 'https://sandbox.safaricom.co.ke'

    def _get_oauth_token(self):
        """Return a cached access token, fetching a new one shortly before it expires."""
        if self.disabled:
            raise MpesaError('M-Pesa client not configured (consumer key/secret missing)')
        if self.token and time.time() < self.token_expires_at:
            return self.token

        url = f"{self._base_url()}/oauth/v1/generate?grant_type=client_credentials"
        auth = (self.consumer_key, self.consumer_secret)
        r = requests.get(url, auth=auth, timeout=REQUEST_TIMEOUT)
        if r.status_code >= 400:
            print(f"Safaricom OAuth failed with status {r.status_code}: {r.text}", flush=True)
            raise MpesaError('Could not authenticate with M-Pesa. Check MPESA_CONSUMER_KEY / MPESA_CONSUMER_SECRET.')
        data = r.json()
        self.token = data['access_token']
        # Tokens last 3600s; refresh a minute early
        self.token_expires_at = time.time() + int(data.get('expires_in', 3599)) - 60
        return self.token

    def stk_push(self, phone_number: str, amount: float, account_reference: str, transaction_desc: str = 'Payment'):
        """Send STK Push (Lipa na M-PESA Online). Returns the API response as dict.

        phone_number must be in 2547XXXXXXXX / 2541XXXXXXXX format.
        account_reference is limited to 12 characters and transaction_desc to 13 by Daraja.
        """
        if self.disabled:
            raise MpesaError('M-Pesa not configured. Set MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET to enable payments.')

        if not self.shortcode or not self.passkey:
            raise MpesaError('MPESA_SHORTCODE and MPESA_PASSKEY must be configured to perform STK Push')

        token = self._get_oauth_token()

        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()

        url = f"{self._base_url()}/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(round(amount)),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": os.getenv('MPESA_CALLBACK_URL', 'https://example.com/mpesa/callback'),
            "AccountReference": account_reference[:12],
            "TransactionDesc": transaction_desc[:13]
        }
        r = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        if r.status_code >= 400:
            print(f"Safaricom STK Push failed with status {r.status_code}: {r.text}", flush=True)
            if r.status_code == 401:
                # token was revoked early; force a fresh one next time
                self.token = None
            try:
                message = r.json().get('errorMessage')
            except ValueError:
                message = None
            raise MpesaError(f"M-Pesa rejected the request: {message or r.status_code}")
        return r.json()

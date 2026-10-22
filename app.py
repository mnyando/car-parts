import os
import re
import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()

from firebase_config import get_firestore_client
from mpesa import MpesaClient, MpesaError
from catalog import BASE_PRODUCTS, get_product, frontend_config

MAX_QUANTITY = 99
MAX_CART_LINES = 50

app = Flask(__name__)

# Initialize Firebase (optional)
try:
    db = get_firestore_client()
    FIRESTORE_ENABLED = True
except Exception:
    # Firestore not configured; fall back to a simple local JSON store for development
    import json
    import uuid
    ORDERS_FILE = 'local_orders.json'
    FIRESTORE_ENABLED = False

    class LocalOrders:
        def __init__(self, path):
            self.path = path
            try:
                with open(self.path, 'r') as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

        def _save(self):
            with open(self.path, 'w') as f:
                json.dump(self._data, f, indent=2)

        def collection(self, name):
            # only support 'orders'
            return self

        def document(self, doc_id=None):
            if doc_id is None:
                # generate an id similar to Firestore
                doc_id = str(uuid.uuid4())
            return LocalDocument(self, doc_id)

    class LocalDocument:
        def __init__(self, store, doc_id):
            self.store = store
            self.id = doc_id

        def set(self, data):
            self.store._data[self.id] = data
            self.store._save()

        def update(self, data):
            existing = self.store._data.get(self.id, {})
            existing.update(data)
            self.store._data[self.id] = existing
            self.store._save()

    db = LocalOrders(ORDERS_FILE)

# Initialize Mpesa client
mp = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    env=os.getenv("MPESA_ENV", "sandbox"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY")
)

@app.context_processor
def inject_catalog_config():
    return {"catalog_config": frontend_config()}

@app.route('/')
def index():
    return render_template('landing.html')


@app.route('/catalog')
def catalog():
    return render_template('catalog.html', products=BASE_PRODUCTS)


@app.route('/cart')
def cart():
    return render_template('cart.html')

def normalize_phone(raw):
    """Convert 07XXXXXXXX / 01XXXXXXXX / +2547XXXXXXXX etc. to 2547XXXXXXXX. Returns None if invalid."""
    phone = re.sub(r'[\s\-()]', '', str(raw or ''))
    if phone.startswith('+'):
        phone = phone[1:]
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif len(phone) == 9:
        phone = '254' + phone
    return phone if re.fullmatch(r'254[17]\d{8}', phone) else None


def parse_cart_items(data):
    """Return (lines, error). Accepts {"items": [{"id", "quantity"}]} or legacy {"product_id"}."""
    raw_items = data.get('items')
    if raw_items is None and data.get('product_id'):
        raw_items = [{'id': data.get('product_id'), 'quantity': 1}]
    if not isinstance(raw_items, list) or not raw_items:
        return None, "Your cart is empty"
    if len(raw_items) > MAX_CART_LINES:
        return None, "Too many items in cart"

    lines = {}
    for item in raw_items:
        if not isinstance(item, dict):
            return None, "Invalid cart item"
        product = get_product(item.get('id'))
        if not product:
            return None, f"Product not found: {item.get('id')}"
        try:
            quantity = int(item.get('quantity', 1))
        except (TypeError, ValueError):
            return None, "Invalid quantity"
        if quantity < 1 or quantity > MAX_QUANTITY:
            return None, f"Quantity must be between 1 and {MAX_QUANTITY}"
        line = lines.setdefault(product['id'], {
            'product_id': product['id'],
            'name': product['name'],
            'unit_price': product['price'],
            'quantity': 0,
        })
        line['quantity'] = min(line['quantity'] + quantity, MAX_QUANTITY)

    for line in lines.values():
        line['line_total'] = line['unit_price'] * line['quantity']
    return list(lines.values()), None


@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json(silent=True) or request.form.to_dict()

    phone = normalize_phone(data.get('phone'))
    if not phone:
        return jsonify({"error": "Enter a valid Safaricom number, e.g. 0712345678 or 254712345678"}), 400

    lines, error = parse_cart_items(data)
    if error:
        status = 404 if error.startswith('Product not found') else 400
        return jsonify({"error": error}), status

    # Total is always computed server-side from catalog prices
    amount = sum(line['line_total'] for line in lines)

    # Create order in Firestore (or local fallback)
    order_ref = db.collection('orders').document()
    order_ref.set({
        'items': lines,
        'phone': phone,
        'amount': amount,
        'status': 'pending',
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })

    # Initiate STK Push. Daraja limits AccountReference to 12 characters.
    account_reference = f"CP{order_ref.id[:10]}".upper()
    try:
        res = mp.stk_push(phone_number=phone, amount=amount, account_reference=account_reference, transaction_desc="Car parts")
    except MpesaError as e:
        order_ref.update({'status': 'failed', 'error': str(e)})
        return jsonify({"error": str(e)}), 503
    except Exception as e:  # network errors, timeouts, bad JSON
        print(f"STK Push error for order {order_ref.id}: {e!r}", flush=True)
        order_ref.update({'status': 'failed', 'error': repr(e)})
        return jsonify({"error": "Could not reach M-Pesa, please try again"}), 502

    order_ref.update({
        'account_reference': account_reference,
        'checkout_request_id': res.get('CheckoutRequestID'),
        'mpesa_response': res,
    })
    if str(res.get('ResponseCode')) != '0':
        order_ref.update({'status': 'failed'})
        return jsonify({"error": res.get('ResponseDescription') or "M-Pesa did not accept the request"}), 502

    return jsonify({
        "order_id": order_ref.id,
        "amount": amount,
        "customer_message": res.get('CustomerMessage'),
    })


@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Endpoint to receive M-Pesa STK Push callbacks from Daraja.

    The callback payload typically looks like:
    { "Body": { "stkCallback": { ... , "CallbackMetadata": { "Item": [ {"Name":"AccountReference","Value":"<ref>"}, ... ] } } } }
    """
    payload = request.get_json(silent=True) or {}
    # attempt to extract account reference from callback metadata
    try:
        stk = payload.get('Body', {}).get('stkCallback', {})
        result_code = stk.get('ResultCode')
        result_desc = stk.get('ResultDesc')
        callback_items = stk.get('CallbackMetadata', {}).get('Item', []) or []
        account_ref = None
        mpesa_receipt = None
        amount = None
        for item in callback_items:
            name = item.get('Name')
            if name == 'AccountReference':
                account_ref = item.get('Value')
            if name == 'MpesaReceiptNumber':
                mpesa_receipt = item.get('Value')
            if name == 'Amount':
                amount = item.get('Value')

        if not account_ref:
            # fallback: some callbacks may include AccountReference at other paths
            account_ref = stk.get('AccountReference')

        if not account_ref:
            return jsonify({'error': 'AccountReference not found in callback'}), 400

        # update Firestore order matching the account_ref (we used order id as account_reference)
        order_doc = db.collection('orders').document(account_ref)
        update_data = {'status': 'failed' if result_code != 0 else 'paid', 'mpesa_result': {'code': result_code, 'desc': result_desc, 'receipt': mpesa_receipt, 'amount': amount}}
        order_doc.update(update_data)
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('FLASK_DEBUG') == '1')

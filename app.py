import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()

from firebase_config import get_firestore_client
from mpesa import MpesaClient
from catalog import BASE_PRODUCTS, get_product, frontend_config

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

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.form or request.json
    phone = data.get('phone')
    product_id = data.get('product_id')

    if not phone or not product_id:
        return jsonify({"error": "phone and product_id required"}), 400

    product = get_product(product_id)
    if not product:
        return jsonify({"error": "product not found"}), 404

    amount = product['price']
    # Create order in Firestore (or local fallback)
    order_ref = db.collection('orders').document()
    order_data = {
        'product_id': product_id,
        'phone': phone,
        'amount': amount,
        'status': 'pending'
    }
    order_ref.set(order_data)

    # Initiate STK Push
    try:
        res = mp.stk_push(phone_number=phone, amount=amount, account_reference=order_ref.id, transaction_desc=f"Order {order_ref.id}")
        # save MPesa response with the order (may contain CheckoutRequestID)
        try:
            order_ref.update({'mpesa_response': res})
        except Exception:
            # local store update may behave differently; ignore errors here
            pass
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"order_id": order_ref.id, "mpesa_response": res})


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

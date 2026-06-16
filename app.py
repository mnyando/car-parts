import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()

from firebase_config import get_firestore_client
from mpesa import MpesaClient

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

MAKES_AND_MODELS = {
    "Toyota": ["Vitz", "Fielder", "Corolla", "Harrier", "Land Cruiser", "Probox"],
    "Nissan": ["X-Trail", "Note", "Sylphy", "Wingroad"],
    "Subaru": ["Impreza", "Forester", "Legacy"],
    "Honda": ["Fit", "Civic", "CR-V"],
    "Mazda": ["Demio", "Axela", "CX-5"],
    "Mitsubishi": ["Outlander", "Lancer", "Pajero"],
    "Volkswagen": ["Golf", "Tiguan", "Polo", "Passat"],
    "Mercedes-Benz": ["C-Class", "E-Class", "GLC"],
    "BMW": ["3 Series", "5 Series", "X3", "X5"],
    "Hyundai": ["Tucson", "Elantra", "Santa Fe"]
}

BASE_PRODUCTS = [
    {"id": "p1", "name": "Brake Pad", "price": 3500.00, "image": "brakepad.jpg"},
    {"id": "p2", "name": "Air Filter", "price": 2200.00, "image": "air_filter.jpg"},
    {"id": "p3", "name": "Castrol Motor Oil", "price": 4500.00, "image": "motor_oil.jpg"},
    {"id": "p4", "name": "Car Wheel", "price": 12000.00, "image": "wheel.jpg"},
    {"id": "p5", "name": "Side Mirror", "price": 3200.00, "image": "side_mirror.jpg"},
    {"id": "p6", "name": "Car Battery", "price": 9500.00, "image": "battery.jpg"},
    {"id": "p7", "name": "Coil Springs", "price": 6000.00, "image": "springs.jpg"},
]

PRODUCTS = []
# Add base generic products
for bp in BASE_PRODUCTS:
    PRODUCTS.append(bp)

# Dynamically register compatibility versions
for bp in BASE_PRODUCTS:
    for make, models in MAKES_AND_MODELS.items():
        for model in models:
            specific_id = f"{bp['id']}_{make.lower()}_{model.lower().replace(' ', '_').replace('-', '_')}"
            specific_name = f"{make} {model} {bp['name']}"
            
            # Specific price adjustments based on brand
            price_modifier = 0
            if make in ["Mercedes-Benz", "BMW"]:
                price_modifier = 2500
            elif make in ["Toyota", "Subaru"]:
                price_modifier = 400
            elif make in ["Nissan", "Mazda"]:
                price_modifier = -200
                
            PRODUCTS.append({
                "id": specific_id,
                "name": specific_name,
                "price": bp["price"] + price_modifier,
                "image": bp["image"]
            })

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

    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
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

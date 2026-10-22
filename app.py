import os
import re
import hmac
import time
import datetime
from dotenv import load_dotenv
from flask import Flask, g, render_template, request, jsonify, url_for

load_dotenv()

from firebase_config import get_firestore_client
from mpesa import MpesaClient, MpesaError
from catalog import frontend_config, get_product, list_products, resolve_variant, seed_products
from local_store import LocalStore
from auth import init_auth, is_admin, login_required

MAX_QUANTITY = 99
MAX_CART_LINES = 50
# Minimum seconds between STK Push Query calls for the same order (Safaricom rate-limits)
STK_QUERY_INTERVAL = 10
# Daraja ResultCodes: 0 = paid, 1032 = cancelled by the customer
RESULT_CANCELLED = 1032

app = Flask(__name__)

# Initialize Firebase (optional)
try:
    db = get_firestore_client()
    FIRESTORE_ENABLED = True
except Exception as e:
    # Firestore not configured; fall back to a simple local JSON store for development
    print(f"Firestore unavailable ({e}); using local_db.json", flush=True)
    db = LocalStore('local_db.json', legacy_path='local_orders.json')
    FIRESTORE_ENABLED = False

if seed_products(db):
    print("Seeded default products", flush=True)

# Safaricom can't send our CSRF token, the callback is protected by MPESA_CALLBACK_SECRET instead
init_auth(app, db, csrf_exempt={'mpesa_callback'})

# Initialize Mpesa client
mp = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    env=os.getenv("MPESA_ENV", "sandbox"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY")
)

def image_url(image):
    """Products store either a full image URL or the name of a file in static/images."""
    if not image:
        return url_for('static', filename='images/brakepad.jpg')
    if image.startswith(('http://', 'https://', '/')):
        return image
    return url_for('static', filename='images/' + image)


def adjust_stock(product_id, delta):
    """Atomically add delta to a product's stock (negative to take stock)."""
    ref = db.collection('products').document(product_id)
    try:
        if FIRESTORE_ENABLED:
            from firebase_admin import firestore
            ref.update({'stock': firestore.Increment(delta)})
        else:
            ref.increment('stock', delta)
    except Exception as e:  # product deleted since the order was placed
        print(f"Could not adjust stock for {product_id}: {e}", flush=True)


@app.context_processor
def inject_template_globals():
    return {"catalog_config": frontend_config(), "year": datetime.date.today().year, "image_url": image_url}

ERROR_PAGES = {
    400: ("Something went wrong", "Your session may have expired. Please go back and try again."),
    403: ("Access denied", "You don't have permission to view this page."),
    404: ("Page not found", "The page you're looking for doesn't exist."),
}


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
def error_page(e):
    title, message = ERROR_PAGES[e.code]
    return render_template('error.html', code=e.code, title=title, message=message), e.code


@app.route('/')
def index():
    return render_template('landing.html')


@app.route('/catalog')
@login_required
def catalog():
    return render_template('catalog.html', products=list_products(db))


@app.route('/cart')
@login_required
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
    """Return (lines, error) for {"items": [{"product_id", "options", "quantity"}]}.

    Names and prices come from the database + catalog options, never from the browser.
    Requested quantities are checked against stock.
    """
    raw_items = data.get('items')
    if not isinstance(raw_items, list) or not raw_items:
        return None, "Your cart is empty"
    if len(raw_items) > MAX_CART_LINES:
        return None, "Too many items in cart"

    lines = {}
    products = {}
    for item in raw_items:
        if not isinstance(item, dict):
            return None, "Invalid cart item"
        product_id = item.get('product_id')
        if product_id not in products:
            products[product_id] = get_product(db, product_id)
        product = products[product_id]
        if not product or not product.get('active', True):
            return None, f"Product not found: {product_id}"
        try:
            variant_key, name, unit_price = resolve_variant(product, item.get('options'))
        except ValueError as e:
            return None, str(e)
        try:
            quantity = int(item.get('quantity', 1))
        except (TypeError, ValueError):
            return None, "Invalid quantity"
        if quantity < 1 or quantity > MAX_QUANTITY:
            return None, f"Quantity must be between 1 and {MAX_QUANTITY}"
        line = lines.setdefault((product_id, variant_key), {
            'product_id': product_id,
            'variant': variant_key,
            'name': name,
            'unit_price': unit_price,
            'quantity': 0,
        })
        line['quantity'] = min(line['quantity'] + quantity, MAX_QUANTITY)

    # Stock is tracked per product, shared by all of its variants
    wanted = {}
    for line in lines.values():
        wanted[line['product_id']] = wanted.get(line['product_id'], 0) + line['quantity']
    for product_id, quantity in wanted.items():
        stock = int(products[product_id].get('stock', 0))
        if quantity > stock:
            name = products[product_id]['name']
            return None, f"Only {max(stock, 0)} {name} left in stock" if stock > 0 else f"{name} is out of stock"

    for line in lines.values():
        line['line_total'] = line['unit_price'] * line['quantity']
    return list(lines.values()), None


@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    data = request.get_json(silent=True) or request.form.to_dict()

    phone = normalize_phone(data.get('phone'))
    if not phone:
        return jsonify({"error": "Enter a valid Safaricom number, e.g. 0712345678 or 254712345678"}), 400

    lines, error = parse_cart_items(data)
    if error:
        status = 404 if error.startswith('Product not found') else 409 if 'stock' in error else 400
        return jsonify({"error": error}), status

    # Total is always computed server-side from catalog prices
    amount = sum(line['line_total'] for line in lines)

    # Create order in Firestore (or local fallback)
    order_ref = db.collection('orders').document()
    order_ref.set({
        'user_id': g.user['id'],
        'items': lines,
        'phone': phone,
        'amount': amount,
        'status': 'pending',
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })

    # Initiate STK Push. Daraja limits AccountReference to 12 characters.
    account_reference = ("CP" + re.sub(r'[^A-Za-z0-9]', '', order_ref.id)[:10]).upper()
    try:
        res = mp.stk_push(phone_number=phone, amount=amount, account_reference=account_reference, transaction_desc="Car parts")
    except MpesaError as e:
        order_ref.update({'status': 'failed', 'error': str(e)})
        return jsonify({"error": str(e)}), 503
    except Exception as e:  # network errors, timeouts, bad JSON
        print(f"STK Push error for order {order_ref.id}: {e!r}", flush=True)
        order_ref.update({'status': 'failed', 'error': repr(e)})
        return jsonify({"error": "Could not reach M-Pesa, please try again"}), 502

    checkout_request_id = res.get('CheckoutRequestID')
    order_ref.update({
        'account_reference': account_reference,
        'checkout_request_id': checkout_request_id,
        'mpesa_response': res,
    })
    if checkout_request_id:
        # The STK callback only identifies the payment by CheckoutRequestID
        db.collection('checkout_requests').document(checkout_request_id).set({'order_id': order_ref.id})
    if str(res.get('ResponseCode')) != '0':
        order_ref.update({'status': 'failed'})
        return jsonify({"error": res.get('ResponseDescription') or "M-Pesa did not accept the request"}), 502

    return jsonify({
        "order_id": order_ref.id,
        "reference": account_reference,
        "amount": amount,
        "customer_message": res.get('CustomerMessage'),
    })


def apply_payment_result(order_ref, order, result_code, result_desc, receipt=None, paid_amount=None):
    """Update an order from a Daraja result (callback or STK query). Never downgrades a paid order."""
    if order.get('status') == 'paid':
        return 'paid'
    try:
        result_code = int(result_code)
    except (TypeError, ValueError):
        result_code = -1

    if result_code == 0:
        # Guard against a callback reporting less than the order total
        if paid_amount is not None and float(paid_amount) < int(round(order.get('amount', 0))):
            status = 'amount_mismatch'
        else:
            status = 'paid'
    elif result_code == RESULT_CANCELLED:
        status = 'cancelled'
    else:
        status = 'failed'

    update = {
        'status': status,
        'mpesa_result': {'code': result_code, 'desc': result_desc, 'receipt': receipt, 'amount': paid_amount},
        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    # Take the sold items out of stock exactly once
    if status == 'paid' and not order.get('stock_applied'):
        update['stock_applied'] = True
        for line in order.get('items', []):
            adjust_stock(line['product_id'], -int(line['quantity']))
    order_ref.update(update)
    return status


@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Endpoint to receive M-Pesa STK Push callbacks from Daraja.

    The callback payload looks like:
    { "Body": { "stkCallback": { "MerchantRequestID": "...", "CheckoutRequestID": "ws_CO_...",
        "ResultCode": 0, "ResultDesc": "...",
        "CallbackMetadata": { "Item": [ {"Name": "Amount", "Value": 1}, {"Name": "MpesaReceiptNumber", "Value": "..."}, ... ] } } } }

    Note it does NOT contain the AccountReference, so orders are matched via CheckoutRequestID.
    Daraja doesn't sign callbacks; set MPESA_CALLBACK_SECRET and append ?token=<secret> to
    MPESA_CALLBACK_URL so only Safaricom (who knows the URL) can mark orders as paid.
    """
    secret = os.getenv('MPESA_CALLBACK_SECRET')
    if secret and not hmac.compare_digest(request.args.get('token', ''), secret):
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Unauthorized'}), 403

    payload = request.get_json(silent=True) or {}
    stk = (payload.get('Body') or {}).get('stkCallback') or {}
    checkout_request_id = stk.get('CheckoutRequestID')
    if not checkout_request_id:
        return jsonify({'ResultCode': 1, 'ResultDesc': 'CheckoutRequestID missing'}), 400

    items = {item.get('Name'): item.get('Value') for item in (stk.get('CallbackMetadata') or {}).get('Item', []) or []}

    mapping = db.collection('checkout_requests').document(checkout_request_id).get()
    if not mapping.exists:
        print(f"M-Pesa callback for unknown CheckoutRequestID {checkout_request_id}", flush=True)
        # Acknowledge anyway so Safaricom doesn't keep retrying
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200

    order_ref = db.collection('orders').document(mapping.to_dict()['order_id'])
    order = order_ref.get().to_dict() or {}
    status = apply_payment_result(order_ref, order, stk.get('ResultCode'), stk.get('ResultDesc'),
                                  receipt=items.get('MpesaReceiptNumber'), paid_amount=items.get('Amount'))
    print(f"Order {order_ref.id} -> {status} ({stk.get('ResultDesc')})", flush=True)
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200


@app.route('/orders/<order_id>/status')
@login_required
def order_status(order_id):
    """Payment status for the checkout page to poll. Falls back to an STK Push Query when the
    callback hasn't arrived (e.g. running locally, where Safaricom can't reach the callback URL)."""
    order_ref = db.collection('orders').document(order_id)
    snapshot = order_ref.get()
    if not snapshot.exists:
        return jsonify({'error': 'order not found'}), 404
    order = snapshot.to_dict()
    # Shoppers can only see their own orders (same 404 so ids can't be probed)
    if order.get('user_id') != g.user['id'] and not is_admin():
        return jsonify({'error': 'order not found'}), 404
    status = order.get('status', 'pending')

    checkout_request_id = order.get('checkout_request_id')
    if status == 'pending' and checkout_request_id and time.time() - order.get('last_query_at', 0) >= STK_QUERY_INTERVAL:
        order_ref.update({'last_query_at': time.time()})
        try:
            res = mp.stk_query(checkout_request_id)
            if 'ResultCode' in res:
                status = apply_payment_result(order_ref, order, res.get('ResultCode'), res.get('ResultDesc'))
        except Exception as e:
            # Still being processed, or Safaricom unreachable: keep polling
            print(f"STK query for order {order_id}: {e}", flush=True)

    return jsonify({'order_id': order_id, 'status': status, 'amount': order.get('amount')})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('FLASK_DEBUG') == '1')

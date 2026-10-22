# Car Parts Store

A premium, minimalist e-commerce storefront for car parts

## Stack

- **Frontend**: Custom HTML5, Vanilla CSS3 (monochrome design tokens, CSS grids), JavaScript (interactions and scroll reveals).
- **Backend**: Python (Flask)
- **Database**: Firebase Firestore (Firebase Admin SDK), with a local JSON fallback for development
- **Payment**: Safaricom M-Pesa (Daraja API STK Push)
- **Languages**: English and Swahili
- **License**: MIT License

---

## Features

- **Accounts and roles**: Anyone can sign up as a shopper. Browsing parts, the cart and checkout require logging in. Admins get a dashboard; shoppers only see the shop.
- **Admin dashboard** (`/admin`): Add, edit, hide and delete products, set stock, see low-stock items, view orders with their M-Pesa receipts, and promote other users to admin.
- **Stock levels**: The shop shows In stock / Only N left / Out of stock. Checkout refuses more than is in stock, and stock goes down when M-Pesa confirms the payment.
- **Vehicle / spec selection**: Vehicle-specific parts are matched to one of 20 makes and 164 models common in Kenya; batteries, coil springs and motor oil are chosen by specification. Prices update live.
- **English / Swahili**: The EN / SW switch in the header translates all site text and is remembered for a year. Product names stay as the admin typed them.
- **M-Pesa payment flow**: STK push for the whole cart, with live "payment received / cancelled / failed" status.
- **Minimal fixed header**, **slide-out menu and cart drawer**, **portfolio-style product cards** and **scroll reveals**.

---

## Project Layout

| File | Purpose |
| --- | --- |
| `app.py` | Flask app: shop pages, `/checkout`, `/mpesa/callback`, `/orders/<id>/status` |
| `auth.py` | Signup, login, logout, sessions, CSRF protection, `login_required` / `admin_required` |
| `admin.py` | Admin dashboard: products & stock, orders, users |
| `catalog.py` | Vehicle makes/models, spec options, default products, product lookups and pricing (`resolve_variant`) |
| `i18n.py` | English → Swahili translations and the `/lang/<code>` switch |
| `mpesa.py` | Daraja client: OAuth (cached), STK Push, STK Push Query |
| `local_store.py` | Firestore-like JSON store used when Firebase isn't configured |
| `firebase_config.py` | Firestore client setup |
| `static/cart.js` | Cart, selection modal and checkout UI |

---

## Quick Start

### 1. Installation
Create a Python 3.10+ virtual environment, activate it, and install the required modules:

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the root directory and add the following keys:
```env
# Accounts: long random string used to sign login sessions (required in production)
SECRET_KEY=change_me_to_a_long_random_string
# Whoever signs up / logs in with these emails becomes an admin (comma separated)
ADMIN_EMAIL=you@example.com

# M-Pesa API settings
MPESA_ENV=sandbox
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_CALLBACK_URL=https://yourdomain.com/mpesa/callback?token=choose_a_long_random_string
# Optional but recommended: must match the token in MPESA_CALLBACK_URL
MPESA_CALLBACK_SECRET=choose_a_long_random_string

# Firebase settings (optional - without it data is saved to local_db.json)
FIREBASE_CRED_PATH=serviceAccountKey.json
```

- `SECRET_KEY`: Without it a random key is generated on every start, so everyone is logged out when the server restarts. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`.
- `ADMIN_EMAIL`: Sign up with this email to get the admin dashboard. Admins can promote other users from **Admin → Users**.
- `MPESA_CALLBACK_SECRET`: Daraja callbacks are not signed, so without a secret anyone who finds the callback URL could mark an order as paid. When it is set, `/mpesa/callback` rejects requests whose `?token=` doesn't match.

### 3. Running Locally
Run the Flask server:
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your web browser. Set `FLASK_DEBUG=1` for auto-reload.

On first start the 7 default products (brake pads, air filter, motor oil, wheel, side mirror, battery, coil springs) are created with a stock of 20 each. Without Firebase, products, users and orders are stored in `local_db.json` (ignored by git).

---

## Managing the Shop

Log in with your `ADMIN_EMAIL` account and click **Admin** in the header.

- **Products & stock**: Edit stock directly in the table and press **Save**, toggle **Visible / Hidden**, or **Edit** / **Delete** a product.
- **Add product**: Name, base price, stock, optional description and display order, an image (an `https://` link or one of the built-in images), and a type:
  - *Vehicle-specific*: the customer picks a make and model; Mercedes-Benz, BMW, Audi, Land Rover, Lexus and Volvo add KSh 2,500, Toyota and Subaru add KSh 400, Nissan and Mazda subtract KSh 200.
  - *Simple*: no options, added to the cart directly.
  - *Battery*, *Coil springs*, *Motor oil*: the customer picks from the fixed specification options, which adjust the price.
- **Stock** is one number per product, shared by all its variants (e.g. Toyota and BMW brake pads). It goes down when a payment is confirmed; cancelled or failed payments don't touch it.
- **Orders**: Filter by status; paid orders show the M-Pesa receipt number.
- **Users**: Promote shoppers to admin or back. You can't remove your own admin role.

The vehicle list, price adjustments and spec options live in `catalog.py`. Translations live in `i18n.py`: add the English text as the key and the Swahili as the value.

---

## Payment Flow

1. The browser sends the cart (`[{product_id, options, quantity}]`) and phone number to `POST /checkout`. The server re-prices every item from the database and `catalog.py` - the browser's prices are never trusted - checks stock, and accepts phone numbers as `07XXXXXXXX`, `01XXXXXXXX`, `+254...` or `254...`.
2. The server saves the order (`pending`, linked to the logged-in user) and sends an STK Push. The customer sees the order reference (`CP...`) on their phone.
3. Safaricom calls `MPESA_CALLBACK_URL`; the order is matched by `CheckoutRequestID` and marked `paid`, `cancelled`, `failed` or `amount_mismatch`. Paid orders take their items out of stock.
4. Meanwhile the browser polls `GET /orders/<id>/status` (shoppers can only see their own orders). If the callback hasn't arrived (e.g. when running locally, where Safaricom can't reach your machine), the server asks Safaricom directly with an STK Push Query, at most every 10 seconds.
5. The cart is cleared only once the payment is confirmed.

---

## Deployment to Render

To deploy this project to [Render](https://render.com) as a Web Service:

1. Connect your GitHub repository.
2. Configure basic settings:
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 1 --threads 8 --bind 0.0.0.0:$PORT`
3. Add Environment Variables under **Advanced Settings** for `SECRET_KEY`, `ADMIN_EMAIL`, `MPESA_ENV`, `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`, `MPESA_PASSKEY`, `MPESA_CALLBACK_URL` and `MPESA_CALLBACK_SECRET`. The callback URL is `https://<your-service>.onrender.com/mpesa/callback?token=<MPESA_CALLBACK_SECRET>`.
4. Upload your Firebase credentials as a **Secret File** named `serviceAccountKey.json` and set `FIREBASE_CRED_PATH` to `./serviceAccountKey.json`.

Use Firestore in production: Render's disk is wiped on every deploy, so the `local_db.json` fallback would lose products, users and orders. Keep `--workers 1` if you ever run without Firestore, since each worker would otherwise keep its own copy of the local file. Login cookies are marked secure automatically on Render.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

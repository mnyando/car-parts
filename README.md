# Car Parts Store

A premium, minimalist e-commerce storefront for car parts

## Stack

- **Frontend**: Custom HTML5, Vanilla CSS3 (monochrome design tokens, CSS grids), JavaScript (interactions and scroll reveals).
- **Backend**: Python (Flask)
- **Database**: Firebase Firestore (Firebase Admin SDK), with a local JSON fallback for development
- **Payment**: Safaricom M-Pesa (Daraja API STK Push)
- **License**: MIT License

---

## Features

- **Minimal fixed header**: Blends with difference blend mode for readability over any image.
- **Slide-out navigation menu**: Oversized links with micro-animation hover fades.
- **Slide-out Cart drawer**: Tracks selected products, quantities and totals on every page; the `/cart` page shows the same cart.
- **Vehicle / spec selection**: Brake pads, air filters, wheels and mirrors are matched to a make and model; batteries, coil springs and motor oil are chosen by specification. Prices update live.
- **Portfolio-style product cards**: Two-column layouts on desktop transitioning to single-column on mobile.
- **Interactive scroll reveals**: Standard `IntersectionObserver` reveals modules as the user scrolls.
- **M-Pesa payment flow**: STK push for the whole cart, with live "payment received / cancelled / failed" status.

---

## Project Layout

| File | Purpose |
| --- | --- |
| `app.py` | Flask routes: pages, `/checkout`, `/mpesa/callback`, `/orders/<id>/status` |
| `catalog.py` | Single source of truth for products, options and prices (also sent to the browser as `window.CATALOG`) |
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
# M-Pesa API settings
MPESA_ENV=sandbox
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_CALLBACK_URL=https://yourdomain.com/mpesa/callback?token=choose_a_long_random_string
# Optional but recommended: must match the token in MPESA_CALLBACK_URL
MPESA_CALLBACK_SECRET=choose_a_long_random_string

# Firebase settings (optional - without it orders are saved to local_orders.json)
FIREBASE_CRED_PATH=serviceAccountKey.json
```

`MPESA_CALLBACK_SECRET`: Daraja callbacks are not signed, so without a secret anyone who finds the callback URL could mark an order as paid. When it is set, `/mpesa/callback` rejects requests whose `?token=` doesn't match.

### 3. Running Locally
Run the Flask server:
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your web browser. Set `FLASK_DEBUG=1` for auto-reload.

---

## Payment Flow

1. The browser sends the cart (`[{id, quantity}]`) and phone number to `POST /checkout`. The server re-prices every item from `catalog.py` - the browser's prices are never trusted - and accepts phone numbers as `07XXXXXXXX`, `01XXXXXXXX`, `+254...` or `254...`.
2. The server saves the order (`pending`) and sends an STK Push. The customer sees the order reference (`CP...`) on their phone.
3. Safaricom calls `MPESA_CALLBACK_URL`; the order is matched by `CheckoutRequestID` and marked `paid`, `cancelled`, `failed` or `amount_mismatch`.
4. Meanwhile the browser polls `GET /orders/<id>/status`. If the callback hasn't arrived (e.g. when running locally, where Safaricom can't reach your machine), the server asks Safaricom directly with an STK Push Query, at most every 10 seconds.
5. The cart is cleared only once the payment is confirmed.

---

## Deployment to Render

To deploy this project to [Render](https://render.com) as a Web Service:

1. Connect your GitHub repository.
2. Configure basic settings:
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 1 --threads 8 --bind 0.0.0.0:$PORT`
3. Add Environment Variables under **Advanced Settings** for `MPESA_ENV`, `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`, `MPESA_PASSKEY`, `MPESA_CALLBACK_URL` and `MPESA_CALLBACK_SECRET`. The callback URL is `https://<your-service>.onrender.com/mpesa/callback?token=<MPESA_CALLBACK_SECRET>`.
4. Upload your Firebase credentials as a **Secret File** named `serviceAccountKey.json` and set `FIREBASE_CRED_PATH` to `./serviceAccountKey.json`.

Use Firestore in production: Render's disk is wiped on every deploy, so the `local_orders.json` fallback would lose orders. Keep `--workers 1` if you ever run without Firestore, since each worker would otherwise keep its own copy of the local file.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

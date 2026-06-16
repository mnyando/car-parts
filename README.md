# Car Parts Store

A premium, minimalist e-commerce storefront for car parts

## Stack

- **Frontend**: Custom HTML5, Vanilla CSS3 (monochrome design tokens, CSS grids), JavaScript (interactions and scroll reveals).
- **Backend**: Python (Flask)
- **Database**: Firebase Firestore (Firebase Admin SDK)
- **Payment**: Safaricom M-Pesa (Daraja API STK Push)
- **License**: MIT License

---

## Features

- **Minimal fixed header**: Blends with difference blend mode for readability over any image.
- **Slide-out navigation menu**: Oversized links with micro-animation hover fades.
- **Slide-out Cart drawer**: Tracks selected products, total prices, and handles checkout processes dynamically.
- **Portfolio-style product cards**: Two-column layouts on desktop transitioning to single-column on mobile.
- **Interactive scroll reveals**: Standard `IntersectionObserver` reveals modules as the user scrolls.
- **M-Pesa payment flow**: Integrated STK push checkout form.

---

## Quick Start

### 1. Installation
Create a Python 3.10+ virtual environment, activate it, and install the required modules:
```bash
python3 -m venv .venv
source .venv/bin/activate
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
MPESA_CALLBACK_URL=https://yourdomain.com/mpesa/callback

# Firebase settings
FIREBASE_CRED_PATH=serviceAccountKey.json
```

### 3. Running Locally
Run the Flask server:
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your web browser.

---

## Deployment to Render

To deploy this project to [Render](https://render.com) as a Web Service:

1. Connect your GitHub repository.
2. Configure basic settings:
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
3. Add Environment Variables under **Advanced Settings** for `MPESA_ENV`, `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`, `MPESA_PASSKEY`, and `MPESA_CALLBACK_URL`.
4. Upload your Firebase credentials as a **Secret File** named `serviceAccountKey.json` and set `FIREBASE_CRED_PATH` to `./serviceAccountKey.json`.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

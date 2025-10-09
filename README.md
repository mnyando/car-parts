Car Parts Website

This repository is a starter skeleton for a car parts e-commerce site using:
- Frontend: HTML/CSS (templates)
- Backend: Python (Flask)
- Database: Firebase Firestore (Firebase Admin SDK)
- Payment: M-Pesa (via Daraja API / STK Push)

What you get:
- A minimal Flask app with product catalog, checkout flow, and an M-Pesa module.
- Firebase integration to store orders.
- Environment configuration via .env

Quick start
1. Create a Python 3.10+ virtualenv and activate it.
2. Install requirements: pip install -r requirements.txt
3. Create a Firebase service account JSON and set FIREBASE_CRED_PATH to its path.
4. Populate .env with your M-Pesa consumer key & secret and other values.
5. Run the app: python app.py

Notes
- The STK Push requires a shortcode and passkey (not provided). The mpesa module supports sandbox and production; set MPESA_ENV accordingly.
- The consumer key/secret you provided should be kept secret; store them in environment variables.

Files
- app.py: Flask application and routes
- mpesa.py: M-Pesa integration (OAuth + STK Push)
- firebase_config.py: initializes Firestore client
- templates/: HTML templates
- static/: CSS files
- .env.example: example configuration

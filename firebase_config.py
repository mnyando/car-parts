import os
import firebase_admin
from firebase_admin import credentials, firestore

def get_firestore_client():
    cred_path = os.getenv('FIREBASE_CRED_PATH')
    if not cred_path:
        raise RuntimeError('FIREBASE_CRED_PATH environment variable not set')
    cred = credentials.Certificate(cred_path)
    try:
        app = firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(cred)
    return firestore.client()

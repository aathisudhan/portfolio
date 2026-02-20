import os
import json
import firebase_admin
from firebase_admin import credentials, db

# 1. Database URL from Render environment or fallback
DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL', 'https://portfolio-imgn-default-rtdb.asia-southeast1.firebasedatabase.app/')

def initialize_firebase():
    if firebase_admin._apps:
        return

    # Render places "Secret Files" in /etc/secrets/
    render_secret_path = '/etc/secrets/FIREBASE_SERVICE_ACCOUNT'
    local_path = 'serviceAccount.json'

    if os.path.exists(render_secret_path):
        # Case: On Render (using Secret File)
        cred_path = render_secret_path
        print("Using Render Secret File for Firebase.")
    elif os.path.exists(local_path):
        # Case: Local development
        cred_path = local_path
        print("Using local serviceAccount.json for Firebase.")
    else:
        print("CRITICAL: No Firebase credentials found!")
        return

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
        print(f"Firebase initialized successfully with DB: {DATABASE_URL}")
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")

# Run initialization
initialize_firebase()

def get_db():
    return db

def get_portfolio_ref():
    try:
        return db.reference('portfolio')
    except Exception:
        return None

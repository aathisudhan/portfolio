import os
import firebase_admin
from firebase_admin import credentials, db

# Preferred explicit DB URL (from your instruction)
DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL', 'https://portfolio-imgn-default-rtdb.asia-southeast1.firebasedatabase.app/')

def initialize_firebase():
    if firebase_admin._apps:
        return
    cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccount.json')
    if not os.path.exists(cred_path):
        print(f"Warning: service account not found at {cred_path}")
        return
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
        print(f"Firebase initialized with DB URL: {DATABASE_URL}")
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")

# Initialize on import (idempotent)
initialize_firebase()

def get_db():
    """Return the `firebase_admin.db` module for making references.
    Example usage: get_db().reference('portfolio').get()
    """
    return db

def get_portfolio_ref():
    """Convenience: return reference to the `portfolio` node."""
    try:
        return get_db().reference('portfolio')
    except Exception:
        return None

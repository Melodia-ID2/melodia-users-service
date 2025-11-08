import firebase_admin
from firebase_admin import credentials
from pathlib import Path

_firebase_initialized = False


def initialize_firebase():
    global _firebase_initialized
    
    if _firebase_initialized:
        return
    
    cred_path = "config/firebase-service-account.json"
    if not Path(cred_path).exists():
        raise FileNotFoundError(
            f"Firebase credentials not found at {cred_path}."
        )
    
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

    _firebase_initialized = True


def get_firebase_app():
    if not _firebase_initialized:
        initialize_firebase()
    return firebase_admin.get_app()
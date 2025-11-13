import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials


def _service_account_path() -> str:
    return os.getenv("FIREBASE_CREDENTIALS_PATH", "config/firebase-service-account.json")


def initialize_firebase() -> None:
    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    cred_path = _service_account_path()
    if Path(cred_path).exists():
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        return

    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)


def get_firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        initialize_firebase()
        return firebase_admin.get_app()

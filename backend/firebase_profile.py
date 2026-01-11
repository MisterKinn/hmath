import firebase_admin
from firebase_admin import credentials, auth, firestore
from .firebase_account import firebase_config
import os

# Initialize Firebase app (singleton)
_firebase_app = None

def get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        cred = credentials.Certificate(firebase_config)
        _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app

def get_user_profile(uid: str):
    """
    Fetch user profile info from Firebase Auth and Firestore.
    Returns: dict with keys: display_name, email, photo_url, tier (if available)
    """
    app = get_firebase_app()
    user = auth.get_user(uid, app=app)
    profile = {
        'display_name': user.display_name,
        'email': user.email,
        'photo_url': user.photo_url,
        'uid': user.uid,
    }
    # Optionally fetch extra info from Firestore (e.g., user tier)
    db = firestore.client(app=app)
    doc = db.collection('users').document(uid).get()
    if doc.exists:
        data = doc.to_dict()
        if 'tier' in data:
            profile['tier'] = data['tier']
    return profile

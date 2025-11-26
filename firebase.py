import firebase_admin
from firebase_admin import credentials, db
from fire_config import firebaseConfig

if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": firebaseConfig["projectId"],
        "private_key_id": "fake",
        "private_key": "-----BEGIN PRIVATE KEY-----\nFAKEKEY\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk@test",
        "client_id": "1",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": ""
    })

    firebase_admin.initialize_app(cred, {
        "databaseURL": firebaseConfig["databaseURL"]
    })

game_ref = db.reference("game")
players_ref = db.reference("players")
answers_ref = db.reference("answers")
timer_ref = db.reference("timer")
stats_ref = db.reference("stats")

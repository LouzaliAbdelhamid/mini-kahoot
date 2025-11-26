import pyrebase
from fire_config import firebaseConfig

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

# Database references
game_ref = db.child("game")
players_ref = db.child("players")
answers_ref = db.child("answers")
timer_ref = db.child("timer")
stats_ref = db.child("stats")

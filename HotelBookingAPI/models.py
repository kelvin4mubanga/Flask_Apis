from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(100))
    room_number = db.Column(db.Integer)
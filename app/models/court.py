from app import db
from datetime import datetime, timezone
from sqlalchemy import Time
from datetime import time  # Añade esta importación

class Court(db.Model):
    __tablename__ = 'courts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sport_type = db.Column(db.String(50), nullable=False)  # futbol, tenis, basquet
    capacity = db.Column(db.Integer, nullable=False)
    hourly_rate = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    opening_time = db.Column(Time, nullable=False, default=time(8, 0))   # Cambiado a objeto time
    closing_time = db.Column(Time, nullable=False, default=time(22, 0))  # Cambiado a objeto time
    
    # Relationships
    reservations = db.relationship('Reservation', backref='court', lazy=True)
    
    def __repr__(self):
        return f'<Court {self.name} - {self.sport_type}>'
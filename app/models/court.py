from app import db
from datetime import datetime
from sqlalchemy import Time

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    opening_time = db.Column(Time, nullable=False, default='08:00:00')   # <-- Agregado
    closing_time = db.Column(Time, nullable=False, default='22:00:00')   # <-- Agregado
    
    # Relationships
    reservations = db.relationship('Reservation', backref='court', lazy=True)
    
    def __repr__(self):
        return f'<Court {self.name} - {self.sport_type}>'
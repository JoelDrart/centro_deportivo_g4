from app import db
from datetime import datetime
from enum import Enum

class ReservationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(ReservationStatus), default=ReservationStatus.PENDING)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='reservation', lazy=True)
    
    def get_duration_hours(self):
        return (self.end_time - self.start_time).total_seconds() / 3600
    
    def is_active(self):
        return self.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
    
    def __repr__(self):
        return f'<Reservation {self.id} - {self.court.name}>'
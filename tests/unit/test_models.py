import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.models.court import Court
from app.models.reservation import Reservation, ReservationStatus
from app.models.payment import Payment, PaymentStatus, PaymentMethod

def test_user_creation(init_database):
    user = User.query.first()
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.get_full_name() == "Test User"
    assert user.check_password("password123") is True
    assert user.check_password("wrongpass") is False

def test_court_creation(init_database):
    court = Court.query.first()
    assert court.name == "Test Court"
    assert court.sport_type == "futbol"
    assert court.capacity == 10
    assert court.hourly_rate == 50.0

def test_reservation_creation(init_database):
    reservation = Reservation.query.first()
    assert reservation.user_id == 1
    assert reservation.court_id == 1
    assert reservation.total_amount == 100.0
    assert reservation.status == ReservationStatus.PENDING
    assert reservation.is_active() is True

def test_reservation_status_changes(init_database):
    reservation = Reservation.query.first()
    
    reservation.status = ReservationStatus.CONFIRMED
    assert reservation.is_active() is True
    
    reservation.status = ReservationStatus.CANCELLED
    assert reservation.is_active() is False

def test_payment_creation(init_database):
    payment = Payment(
        user_id=1,
        reservation_id=1,
        amount=100.0,
        payment_method=PaymentMethod.CREDIT_CARD,
        transaction_id="TEST123"
    )
    db.session.add(payment)
    db.session.commit()
    
    assert payment.amount == 100.0
    assert payment.status == PaymentStatus.PENDING
    assert payment.payment_method == PaymentMethod.CREDIT_CARD
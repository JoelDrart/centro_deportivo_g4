import pytest
from app.models.payment import PaymentMethod, PaymentStatus
from app.models.reservation import ReservationStatus

from datetime import datetime, timedelta, time
from app.services.reservation_service import ReservationService
from app.services.payment_service import PaymentService
from app.models import db, User, Court, Reservation, Payment

def test_check_availability(init_database):
    court = Court.query.first()
    user = User.query.first()
    
    # Horario disponible (días 2 y 3 están libres)
    available = ReservationService.check_availability(
        court.id,
        datetime.now() + timedelta(days=2),
        datetime.now() + timedelta(days=2, hours=1)
    )
    assert available is True
    
    # Horario ocupado (día 1 está ocupado por la reserva del fixture)
    occupied = ReservationService.check_availability(
        court.id,
        datetime.now() + timedelta(days=1),
        datetime.now() + timedelta(days=1, hours=1)
    )
    assert occupied is False

def test_create_reservation(init_database):
    court = Court.query.first()
    user = User.query.first()
    
    # Usar horario dentro del horario de la cancha (8:00 - 22:00)
    start_time = datetime.now() + timedelta(days=3)
    start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1.5)
    
    reservation = ReservationService.create_reservation(
        user.id,
        court.id,
        start_time,
        end_time,
        "Test note"
    )
    
    assert reservation is not None
    assert reservation.user_id == user.id
    assert reservation.court_id == court.id
    assert reservation.total_amount == 75.0  # 1.5 horas * 50.0
    assert reservation.notes == "Test note"

def test_confirm_reservation(init_database):
    reservation = Reservation.query.first()
    
    confirmed_reservation = ReservationService.confirm_reservation(reservation.id)
    
    assert confirmed_reservation.status == ReservationStatus.CONFIRMED

def test_process_payment(init_database):
    reservation = Reservation.query.first()
    user = User.query.first()
    
    payment = PaymentService.process_payment(
        user.id,
        reservation.id,
        PaymentMethod.CREDIT_CARD,
        100.0
    )
    
    assert payment is not None
    assert payment.reservation_id == reservation.id
    assert payment.amount == 100.0
    assert payment.payment_method == PaymentMethod.CREDIT_CARD
    assert payment.status in [PaymentStatus.COMPLETED, PaymentStatus.FAILED]
from flask import current_app
import pytest
from app import db
from unittest.mock import patch
from datetime import datetime, time, timedelta
from app.models.court import Court
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User
from app.services import ReservationService, PaymentService

def test_integration_reservation_payment_email(init_database):
    user = db.session.get(User, 1)
    court = db.session.get(Court, 1)
    # Ajustar horario para que esté dentro del rango 8:00-22:00
    start_time = datetime.now().replace(hour=10, minute=0) + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    
    with patch('app.services.email_service.EmailService.send_email'), \
         patch('app.services.payment_service.PaymentService._simulate_payment_gateway', return_value=True):
        
        reservation = ReservationService.create_reservation(user.id, court.id, start_time, end_time)
        payment = PaymentService.process_payment(
            user.id, 
            reservation.id, 
            PaymentMethod.CREDIT_CARD,
            reservation.total_amount
        )
        assert payment.status == PaymentStatus.COMPLETED

def test_integration_cancel_reservation_refund(init_database):
    reservation = db.session.get(Reservation, 1)
    reservation.status = ReservationStatus.CONFIRMED
    db.session.commit()
    
    payment = Payment(
        user_id=1,
        reservation_id=reservation.id,
        amount=100.0,
        payment_method=PaymentMethod.CREDIT_CARD,  # ← Usar el enum
        status=PaymentStatus.COMPLETED
    )
    db.session.add(payment)
    db.session.commit()
    
    # Cancelar reserva y verificar reembolso
    with patch('app.services.email_service.EmailService.send_email'):
        cancelled_reservation = ReservationService.cancel_reservation(reservation.id)
        updated_payment = db.session.get(Payment, payment.id)
        
        assert cancelled_reservation.status == ReservationStatus.CANCELLED
        assert updated_payment.status == PaymentStatus.REFUNDED
        
def test_integration_court_hours_availability(init_database):
    court = db.session.get(Court, 1)
    court.opening_time = time(8, 0)
    court.closing_time = time(20, 0)
    db.session.commit()
    
    start_time = datetime.now().replace(hour=21, minute=0)  # 9 PM (fuera de horario)
    end_time = start_time + timedelta(hours=1)
    
    with pytest.raises(ValueError):
        ReservationService.create_reservation(1, court.id, start_time, end_time)
        
def test_integration_user_multiple_reservations(db_session, sample_user, sample_court):
    # Horarios dentro del rango permitido
    reservation1 = ReservationService.create_reservation(
        sample_user.id, sample_court.id,
        datetime.now().replace(hour=10, minute=0) + timedelta(days=1),
        datetime.now().replace(hour=11, minute=0) + timedelta(days=1)
    )
    
    reservation2 = ReservationService.create_reservation(
        sample_user.id, sample_court.id,
        datetime.now().replace(hour=14, minute=0) + timedelta(days=2),
        datetime.now().replace(hour=15, minute=0) + timedelta(days=2)
    )
    
    # Refrescar el usuario para obtener las relaciones actualizadas
    db_session.refresh(sample_user)
    assert len(sample_user.reservations) == 2
    
    
def test_integration_failed_payment_reservation_status(init_database):
    with current_app.app_context():  # Add this
        reservation = db.session.get(Reservation, 1)
        with patch('app.services.payment_service.PaymentService._simulate_payment_gateway', return_value=False):
            payment = PaymentService.process_payment(
                user_id=1,
                reservation_id=reservation.id,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=100.0
            )
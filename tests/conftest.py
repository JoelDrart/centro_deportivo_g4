import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app, db
from app.models.user import User
from app.models.court import Court
from app.models.reservation import Reservation, ReservationStatus
from datetime import datetime, time, timedelta
from app.config import TestingConfig

@pytest.fixture(scope='module')
def test_app():
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        
        
@pytest.fixture(scope='module')
def test_client(test_app):
    return test_app.test_client()

@pytest.fixture
def init_database(test_app):
    db.create_all()
    user = User(username="testuser", email="test@example.com", first_name="Test", last_name="User")
    user.set_password("password123")
    db.session.add(user)
    
    court = Court(
        name="Test Court",
        sport_type="futbol",
        capacity=10,
        hourly_rate=50.0,
        opening_time=time(8, 0),
        closing_time=time(22, 0)
    )
    db.session.add(court)
    db.session.commit()
    
    # Reserva en un horario que no interfiera con las pruebas
    # Cambiamos el estado a PENDING para que el test funcione correctamente
    reservation = Reservation(
        user_id=user.id,
        court_id=court.id,
        start_time=datetime.now() + timedelta(days=1),  # Reserva para mañana
        end_time=datetime.now() + timedelta(days=1, hours=1),
        total_amount=100.0,
        status=ReservationStatus.PENDING  # Cambiado de CONFIRMED a PENDING
    )
    db.session.add(reservation)
    db.session.commit()
    
    yield db
    db.session.remove()
    db.drop_all()
    
@pytest.fixture(scope='module')
def app():
    """Fixture de aplicación con contexto"""
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def client(app):
    """Fixture de cliente de prueba"""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Fixture de sesión de base de datos para cada test"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()

@pytest.fixture
def sample_user(db_session):
    """Fixture de usuario de prueba"""
    user = User(username="testuser", email="test@example.com", first_name="Test", last_name="User")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_court(db_session):
    """Fixture de cancha de prueba"""
    court = Court(
        name="Test Court",
        sport_type="futbol",
        capacity=10,
        hourly_rate=50.0,
        opening_time=time(8, 0),
        closing_time=time(22, 0)
    )
    db_session.add(court)
    db_session.commit()
    return court
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app, db
from app.models.user import User
from app.models.court import Court
from app.models.reservation import Reservation
from datetime import datetime, time, timedelta
from app.config import TestingConfig

@pytest.fixture(scope='module')
def test_app():
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    return test_app.test_client()

@pytest.fixture
def init_database(test_app):
    db.create_all()
    
    user = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )
    user.set_password("password123")
    db.session.add(user)
    
    court = Court(
        name="Test Court",
        sport_type="futbol",
        capacity=10,
        hourly_rate=50.0,
        opening_time=time(8, 0),  # Añade esto
        closing_time=time(22, 0)   # Añade esto
    )
    db.session.add(court)
    
    reservation = Reservation(
        user_id=1,
        court_id=1,
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=2),
        total_amount=100.0
    )
    db.session.add(reservation)
    
    db.session.commit()
    
    yield db
    
    db.session.remove()
    db.drop_all()

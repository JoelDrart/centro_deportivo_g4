import pytest
from app import create_app, db
from app.models.user import User
from app.models.court import Court
from app.models.reservation import Reservation
from datetime import datetime, timedelta

@pytest.fixture(scope='module')
def test_app():
    app = create_app('testing')
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///centro_deportivo.db",
        "WTF_CSRF_ENABLED": False
    })
    
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
    
    # Crear datos de prueba
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
        hourly_rate=50.0
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
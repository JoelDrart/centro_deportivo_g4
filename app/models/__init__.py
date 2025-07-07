from .user import User
from .court import Court
from .reservation import Reservation
from .payment import Payment
from app import db


# Hacer disponibles todas las clases de modelos
__all__ = ['User', 'Court', 'Reservation', 'Payment']

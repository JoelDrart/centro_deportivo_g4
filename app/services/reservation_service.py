from app.models.user import db
from app.models.reservation import Reservation, ReservationStatus
from app.models.court import Court
from app.services.email_service import EmailService
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

class ReservationService:
    @staticmethod
    def check_availability(court_id, start_time, end_time, exclude_reservation_id=None):
        """Verificar disponibilidad de una cancha en un horario específico"""
        query = db.session.query(Reservation).filter(
            and_(
                Reservation.court_id == court_id,
                Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
                or_(
                    and_(Reservation.start_time <= start_time, Reservation.end_time > start_time),
                    and_(Reservation.start_time < end_time, Reservation.end_time >= end_time),
                    and_(Reservation.start_time >= start_time, Reservation.end_time <= end_time)
                )
            )
        )
        
        if exclude_reservation_id:
            query = query.filter(Reservation.id != exclude_reservation_id)
        
        return query.first() is None
    
    @staticmethod
    def create_reservation(user_id, court_id, start_time, end_time, notes=None):
        """Crear una nueva reserva"""
        # Verificar disponibilidad
        if not ReservationService.check_availability(court_id, start_time, end_time):
            raise ValueError("La cancha no está disponible en el horario seleccionado")
        
        # Obtener cancha para calcular el costo
        court = Court.query.get(court_id)
        if not court:
            raise ValueError("Cancha no encontrada")
        
        # Calcular duración y costo
        duration = (end_time - start_time).total_seconds() / 3600
        total_amount = duration * court.hourly_rate
        
        # Crear reserva
        reservation = Reservation(
            user_id=user_id,
            court_id=court_id,
            start_time=start_time,
            end_time=end_time,
            total_amount=total_amount,
            notes=notes,
            status=ReservationStatus.PENDING
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        return reservation
    
    @staticmethod
    def confirm_reservation(reservation_id):
        """Confirmar una reserva"""
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            raise ValueError("Reserva no encontrada")
        
        reservation.status = ReservationStatus.CONFIRMED
        db.session.commit()
        
        # Enviar confirmación por email
        EmailService.send_reservation_confirmation(reservation.user, reservation)
        
        return reservation
    
    @staticmethod
    def cancel_reservation(reservation_id, user_id=None):
        """Cancelar una reserva"""
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            raise ValueError("Reserva no encontrada")
        
        if user_id and reservation.user_id != user_id:
            raise ValueError("No tienes permisos para cancelar esta reserva")
        
        reservation.status = ReservationStatus.CANCELLED
        db.session.commit()
        
        return reservation
    
    @staticmethod
    def get_user_reservations(user_id, include_cancelled=False):
        """Obtener reservas de un usuario"""
        query = Reservation.query.filter_by(user_id=user_id)
        
        if not include_cancelled:
            query = query.filter(Reservation.status != ReservationStatus.CANCELLED)
        
        return query.order_by(Reservation.start_time.desc()).all()
    
    @staticmethod
    def get_court_schedule(court_id, date):
        """Obtener horarios ocupados de una cancha para una fecha específica"""
        return Reservation.query.filter(
            Reservation.court_id == court_id,
            Reservation.start_time >= datetime.combine(date, datetime.min.time()),
            Reservation.end_time <= datetime.combine(date, datetime.max.time()),
            Reservation.status != 'cancelled'
        ).all()
    
    @staticmethod
    def get_upcoming_reservations(user_id, limit=5):
        """Obtener próximas reservas confirmadas del usuario"""
        now = datetime.now()
        return Reservation.query.filter_by(
            user_id=user_id,
            status=ReservationStatus.CONFIRMED
        ).filter(
            Reservation.start_time > now
        ).order_by(Reservation.start_time.asc()).limit(limit).all()
    
    @staticmethod
    def get_recent_reservations(user_id, limit=5):
        """Obtener reservas recientes del usuario (últimas completadas)"""
        now = datetime.now()
        return Reservation.query.filter_by(
            user_id=user_id,
            status=ReservationStatus.CONFIRMED
        ).filter(
            Reservation.end_time < now
        ).order_by(Reservation.end_time.desc()).limit(limit).all()

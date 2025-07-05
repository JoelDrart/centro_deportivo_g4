from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.reservation import Reservation, ReservationStatus
from app.models.court import Court
from app.models.payment import Payment
from app.services.reservation_service import ReservationService
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal del usuario"""
    # Obtener estadísticas del usuario
    user_stats = get_user_stats(current_user.id)
    
    # Obtener próximas reservas
    upcoming_reservations = ReservationService.get_upcoming_reservations(
        current_user.id, limit=5
    )
    
    # Obtener reservas recientes
    recent_reservations = ReservationService.get_recent_reservations(
        current_user.id, limit=5
    )
    
    # Obtener canchas más populares
    popular_courts = get_popular_courts()
    
    return render_template('dashboard/user_dashboard.html',
                         user_stats=user_stats,
                         upcoming_reservations=upcoming_reservations,
                         recent_reservations=recent_reservations,
                         popular_courts=popular_courts)

@dashboard_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """Estadísticas detalladas del usuario"""
    user_stats = get_detailed_user_stats(current_user.id)
    return render_template('dashboard/stats.html', stats=user_stats)

@dashboard_bp.route('/api/dashboard/chart_data')
@login_required
def get_chart_data():
    """API para obtener datos para gráficos del dashboard"""
    try:
        # Reservas por mes (últimos 6 meses)
        reservations_by_month = get_reservations_by_month(current_user.id)
        
        # Gastos por mes
        expenses_by_month = get_expenses_by_month(current_user.id)
        
        # Deportes más practicados
        sports_distribution = get_sports_distribution(current_user.id)
        
        return jsonify({
            'reservations_by_month': reservations_by_month,
            'expenses_by_month': expenses_by_month,
            'sports_distribution': sports_distribution
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@dashboard_bp.route('/api/dashboard/quick_stats')
@login_required
def get_quick_stats():
    """API para obtener estadísticas rápidas"""
    try:
        stats = get_user_stats(current_user.id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def get_user_stats(user_id):
    """Obtener estadísticas básicas del usuario"""
    now = datetime.now()
    
    # Total de reservas
    total_reservations = Reservation.query.filter_by(user_id=user_id).count()
    
    # Reservas activas
    active_reservations = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.status == ReservationStatus.CONFIRMED,
        Reservation.start_time > now
    ).count()
    
    # Reservas este mes
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    reservations_this_month = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.created_at >= start_of_month
    ).count()
    
    # Gasto total
    total_spent = Payment.query.join(Reservation).filter(
        Reservation.user_id == user_id,
        Payment.status == 'completed'
    ).with_entities(func.sum(Payment.amount)).scalar() or 0
    
    # Gasto este mes
    spent_this_month = Payment.query.join(Reservation).filter(
        Reservation.user_id == user_id,
        Payment.status == 'completed',
        Payment.created_at >= start_of_month
    ).with_entities(func.sum(Payment.amount)).scalar() or 0
    
    return {
        'total_reservations': total_reservations,
        'active_reservations': active_reservations,
        'reservations_this_month': reservations_this_month,
        'total_spent': float(total_spent),
        'spent_this_month': float(spent_this_month)
    }

def get_detailed_user_stats(user_id):
    """Obtener estadísticas detalladas del usuario"""
    basic_stats = get_user_stats(user_id)
    
    # Reservas canceladas
    cancelled_reservations = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.status == ReservationStatus.CANCELLED
    ).count()
    
    # Reservas completadas
    completed_reservations = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.status == ReservationStatus.COMPLETED
    ).count()
    
    # Cancha favorita
    favorite_court = get_favorite_court(user_id)
    
    # Horario preferido
    preferred_time = get_preferred_time(user_id)
    
    return {
        **basic_stats,
        'cancelled_reservations': cancelled_reservations,
        'completed_reservations': completed_reservations,
        'favorite_court': favorite_court,
        'preferred_time': preferred_time
    }

def get_reservations_by_month(user_id, months=6):
    """Obtener reservas por mes"""
    result = []
    now = datetime.now()
    
    for i in range(months):
        # Calcular el mes
        month_date = now - timedelta(days=30 * i)
        start_of_month = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if month_date.month == 12:
            end_of_month = month_date.replace(year=month_date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            end_of_month = month_date.replace(month=month_date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        count = Reservation.query.filter(
            Reservation.user_id == user_id,
            Reservation.created_at >= start_of_month,
            Reservation.created_at < end_of_month
        ).count()
        
        result.append({
            'month': month_date.strftime('%Y-%m'),
            'count': count
        })
    
    return list(reversed(result))

def get_expenses_by_month(user_id, months=6):
    """Obtener gastos por mes"""
    result = []
    now = datetime.now()
    
    for i in range(months):
        # Calcular el mes
        month_date = now - timedelta(days=30 * i)
        start_of_month = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if month_date.month == 12:
            end_of_month = month_date.replace(year=month_date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            end_of_month = month_date.replace(month=month_date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total = Payment.query.join(Reservation).filter(
            Reservation.user_id == user_id,
            Payment.status == 'completed',
            Payment.created_at >= start_of_month,
            Payment.created_at < end_of_month
        ).with_entities(func.sum(Payment.amount)).scalar() or 0
        
        result.append({
            'month': month_date.strftime('%Y-%m'),
            'amount': float(total)
        })
    
    return list(reversed(result))

def get_sports_distribution(user_id):
    """Obtener distribución de deportes/canchas"""
    from sqlalchemy import func
    
    result = Reservation.query.join(Court).filter(
        Reservation.user_id == user_id
    ).with_entities(
        Court.sport_type,
        func.count(Reservation.id).label('count')
    ).group_by(Court.sport_type).all()
    
    return [{
        'sport': sport_type,
        'count': count
    } for sport_type, count in result]

def get_popular_courts(limit=5):
    """Obtener canchas más populares"""
    from sqlalchemy import func
    
    result = Court.query.join(Reservation).filter(
        Court.is_active == True
    ).with_entities(
        Court.id,
        Court.name,
        Court.sport_type,
        func.count(Reservation.id).label('reservation_count')
    ).group_by(Court.id).order_by(
        func.count(Reservation.id).desc()
    ).limit(limit).all()
    
    return [{
        'id': court_id,
        'name': name,
        'sport_type': sport_type,
        'reservation_count': count
    } for court_id, name, sport_type, count in result]

def get_favorite_court(user_id):
    """Obtener cancha favorita del usuario"""
    from sqlalchemy import func
    
    result = Reservation.query.join(Court).filter(
        Reservation.user_id == user_id
    ).with_entities(
        Court.name,
        func.count(Reservation.id).label('count')
    ).group_by(Court.id).order_by(
        func.count(Reservation.id).desc()
    ).first()
    
    return result.name if result else None
def get_preferred_time(user_id):
    """Obtener horario preferido del usuario"""
    from sqlalchemy import func
    result = Reservation.query.filter(
        Reservation.user_id == user_id
    ).with_entities(
        func.extract('hour', Reservation.start_time).label('hour'),
        func.count(Reservation.id).label('count')
    ).group_by(
        func.extract('hour', Reservation.start_time)
    ).order_by(
        func.count(Reservation.id).desc()
    ).first()
    if result:
        hour = int(result.hour)
        return f"{hour:02d}:00"
    return None

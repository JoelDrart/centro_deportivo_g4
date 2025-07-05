from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.court import Court
from app.models.reservation import Reservation
from app.services.reservation_service import ReservationService
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página principal"""
    courts = Court.query.filter_by(is_active=True).all()
    return render_template('index.html', courts=courts)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Panel de usuario"""
    user_reservations = ReservationService.get_user_reservations(current_user.id)
    return render_template('dashboard.html', reservations=user_reservations)

@main_bp.route('/courts')
def courts():
    """Listado de canchas disponibles"""
    courts = Court.query.filter_by(is_active=True).all()
    return render_template('courts.html', courts=courts)

@main_bp.route('/api/available-slots')
def available_slots():
    """API para obtener horarios disponibles"""
    court_id = request.args.get('court_id', type=int)
    date_str = request.args.get('date')
    
    if not court_id or not date_str:
        return jsonify({'error': 'Parámetros requeridos: court_id y date'}), 400
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
    
    # Obtener slots disponibles
    available_slots = ReservationService.get_available_slots(court_id, date)
    
    return jsonify({
        'available_slots': [
            {
                'time': slot.strftime('%H:%M'),
                'available': True
            } for slot in available_slots
        ]
    })

@main_bp.route('/contact')
def contact():
    """Página de contacto"""
    return render_template('contact.html')

@main_bp.route('/about')
def about():
    """Página acerca de"""
    return render_template('about.html')

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models.user import User
from app.models.reservation import Reservation
from app.models.court import Court
from app.models.payment import Payment
from app import db
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorador para requerir permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal del administrador"""
    # Estadísticas generales
    total_users = User.query.count()
    total_reservations = Reservation.query.count()
    total_courts = Court.query.count()
    
    # Reservas del día
    today = datetime.now().date()
    today_reservations = Reservation.query.filter(
        db.func.date(Reservation.start_time) == today
    ).count()
    
    # Ingresos del mes
    current_month = datetime.now().replace(day=1)
    monthly_payments = Payment.query.filter(
        Payment.created_at >= current_month,
        Payment.status == 'completed'
    ).all()
    monthly_revenue = sum(p.amount for p in monthly_payments)
    
    # Reservas recientes
    recent_reservations = Reservation.query.order_by(
        Reservation.created_at.desc()
    ).limit(10).all()
    
    # Usuarios nuevos (últimos 30 días)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_users = User.query.filter(
        User.created_at >= thirty_days_ago
    ).count()
    
    stats = {
        'total_users': total_users,
        'total_reservations': total_reservations,
        'total_courts': total_courts,
        'today_reservations': today_reservations,
        'monthly_revenue': monthly_revenue,
        'new_users': new_users
    }
    
    return render_template('dashboard/admin_dashboard.html', 
                         stats=stats, 
                         recent_reservations=recent_reservations)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Gestión de usuarios"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(User.email.contains(search) | User.name.contains(search))
    
    users = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_user_admin(user_id):
    """Cambiar estado de administrador de un usuario"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'error': 'No puedes modificar tu propio estado de administrador'}), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'administrador' if user.is_admin else 'usuario regular'
    flash(f'Usuario {user.name} ahora es {status}.', 'success')
    
    return jsonify({'success': True, 'is_admin': user.is_admin})

@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Activar/desactivar usuario"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'error': 'No puedes desactivar tu propia cuenta'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activado' if user.is_active else 'desactivado'
    flash(f'Usuario {user.name} ha sido {status}.', 'success')
    
    return jsonify({'success': True, 'is_active': user.is_active})

@admin_bp.route('/courts')
@login_required
@admin_required
def courts():
    """Gestión de canchas"""
    courts = Court.query.all()
    return render_template('admin/courts.html', courts=courts)

@admin_bp.route('/courts/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_court():
    """Crear nueva cancha"""
    if request.method == 'POST':
        name = request.form.get('name')
        court_type = request.form.get('court_type')
        hourly_rate = float(request.form.get('hourly_rate', 0))
        is_active = bool(request.form.get('is_active'))
        
        if not name or not court_type:
            flash('El nombre y tipo de cancha son requeridos.', 'error')
            return render_template('admin/court_form.html')
        
        court = Court(
            name=name,
            court_type=court_type,
            hourly_rate=hourly_rate,
            is_active=is_active
        )
        
        db.session.add(court)
        db.session.commit()
        
        flash(f'Cancha {name} creada exitosamente.', 'success')
        return redirect(url_for('admin.courts'))
    
    return render_template('admin/court_form.html')

@admin_bp.route('/courts/<int:court_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_court(court_id):
    """Editar cancha"""
    court = Court.query.get_or_404(court_id)
    
    if request.method == 'POST':
        court.name = request.form.get('name')
        court.court_type = request.form.get('court_type')
        court.hourly_rate = float(request.form.get('hourly_rate', 0))
        court.is_active = bool(request.form.get('is_active'))
        
        db.session.commit()
        flash(f'Cancha {court.name} actualizada exitosamente.', 'success')
        return redirect(url_for('admin.courts'))
    
    return render_template('admin/court_form.html', court=court)

@admin_bp.route('/courts/<int:court_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_court_active(court_id):
    """Activar/desactivar cancha"""
    court = Court.query.get_or_404(court_id)
    court.is_active = not court.is_active
    db.session.commit()
    
    status = 'activada' if court.is_active else 'desactivada'
    flash(f'Cancha {court.name} ha sido {status}.', 'success')
    
    return jsonify({'success': True, 'is_active': court.is_active})

@admin_bp.route('/reservations')
@login_required
@admin_required
def reservations():
    """Gestión de reservas"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Reservation.query
    if status_filter:
        query = query.filter(Reservation.status == status_filter)
    
    reservations = query.order_by(Reservation.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/reservations.html', 
                         reservations=reservations, 
                         status_filter=status_filter)

@admin_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_reservation(reservation_id):
    """Cancelar reserva"""
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.status == 'cancelled':
        return jsonify({'error': 'La reserva ya está cancelada'}), 400
    
    reservation.status = 'cancelled'
    db.session.commit()
    
    flash(f'Reserva #{reservation.id} cancelada exitosamente.', 'success')
    return jsonify({'success': True})

@admin_bp.route('/payments')
@login_required
@admin_required
def payments():
    """Gestión de pagos"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Payment.query
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    
    payments = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/payments.html', 
                         payments=payments, 
                         status_filter=status_filter)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Página de reportes"""
    return render_template('admin/reports.html')

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API para estadísticas del dashboard"""
    # Reservas por mes (últimos 6 meses)
    months_data = []
    for i in range(6):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        reservations_count = Reservation.query.filter(
            Reservation.created_at >= month_start,
            Reservation.created_at <= month_end
        ).count()
        
        months_data.append({
            'month': month_start.strftime('%B'),
            'reservations': reservations_count
        })
    
    # Ingresos por mes
    revenue_data = []
    for i in range(6):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        payments = Payment.query.filter(
            Payment.created_at >= month_start,
            Payment.created_at <= month_end,
            Payment.status == 'completed'
        ).all()
        
        revenue = sum(p.amount for p in payments)
        revenue_data.append({
            'month': month_start.strftime('%B'),
            'revenue': float(revenue)
        })
    
    return jsonify({
        'reservations_by_month': list(reversed(months_data)),
        'revenue_by_month': list(reversed(revenue_data))
    })

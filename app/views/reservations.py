from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.court import Court
from app.models.reservation import Reservation
from app.services.reservation_service import ReservationService
from app.services.email_service import EmailService
from app.models.user import User
from datetime import datetime, timedelta
import json

reservations_bp = Blueprint('reservations', __name__)

@reservations_bp.route('/courts')
@login_required
def view_courts():
    """Ver todas las canchas disponibles"""
    courts = Court.query.filter_by(is_active=True).all()
    return render_template('reservations/courts.html', courts=courts)

@reservations_bp.route('/make_reservation', methods=['GET', 'POST'])
@login_required
def make_reservation():
    if request.method == 'POST':
        try:
            court_id = int(request.form.get('court_id'))
            date_str = request.form.get('date')
            start_time_str = request.form.get('start_time')
            duration = int(request.form.get('duration'))  # <-- NUEVO
            notes = request.form.get('notes')

            # Convertir strings a datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            start_datetime = datetime.combine(date, start_time)

            # Calcular hora de fin
            end_datetime = start_datetime + timedelta(hours=duration)

            # Validaciones
            if start_datetime <= datetime.now():
                flash('No puedes reservar en el pasado', 'error')
                return redirect(url_for('reservations.make_reservation'))

            if end_datetime <= start_datetime:
                flash('La hora de fin debe ser posterior a la hora de inicio', 'error')
                return redirect(url_for('reservations.make_reservation'))

            # Crear reserva
            reservation = ReservationService.create_reservation(
                user_id=current_user.id,
                court_id=court_id,
                start_time=start_datetime,
                end_time=end_datetime,
                notes=notes
            )

            flash('Reserva creada exitosamente', 'success')
            return redirect(url_for('payments.process_payment', reservation_id=reservation.id))

        except Exception as e:
            print("ERROR AL CREAR RESERVA:", e)
            flash(f'Error al crear la reserva: {e}', 'error')
            return redirect(url_for('reservations.make_reservation'))

    courts = Court.query.filter_by(is_active=True).all()
    return render_template(
        'reservations/make_reservation.html',
        courts=courts,
        datetime=datetime,
        timedelta=timedelta
    )

@reservations_bp.route('/my_reservations')
@login_required
def my_reservations():
    """Ver reservas del usuario actual"""
    reservations = ReservationService.get_user_reservations(current_user.id)
    today = datetime.today().date()
    return render_template('reservations/my_reservations.html', reservations=reservations, today=today)

@reservations_bp.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    try:
        reservation = Reservation.query.get_or_404(reservation_id)
        ReservationService.cancel_reservation(reservation_id, current_user.id)
        # Notificar por email
        EmailService.send_reservation_cancellation(current_user, reservation)
        flash(f'Reserva #{reservation.id} cancelada correctamente.', 'success')
        return jsonify(success=True)
    except ValueError as e:
        flash(f'Error al cancelar la reserva: {str(e)}', 'error')
        return jsonify(success=False, message=str(e)), 400

@reservations_bp.route('/api/court/<int:court_id>/schedule')
@login_required
def api_court_schedule(court_id):
    date_str = request.args.get('date')
    from datetime import datetime
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    reservations = ReservationService.get_court_schedule(court_id, date)
    return jsonify({
        "occupied_slots": [
            {
                "start_time": r.start_time.strftime('%H:%M'),
                "end_time": r.end_time.strftime('%H:%M'),
                "user_id": r.user_id
            }
            for r in reservations
        ]
    })

@reservations_bp.route('/court_schedule/<int:court_id>/<date>')
@login_required
def court_schedule(court_id, date):
    """Página visual para ver el horario de una cancha"""
    court = Court.query.get_or_404(court_id)
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    reservations = ReservationService.get_court_schedule(court_id, selected_date)
    return render_template(
        'reservations/court_schedule.html',
        court=court,
        reservations=reservations,
        selected_date=selected_date
    )
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.reservation import Reservation
from app.models.payment import PaymentMethod
from app.services.payment_service import PaymentService

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/process_payment/<int:reservation_id>')
@login_required
def process_payment(reservation_id):
    """Mostrar página de pago"""
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.user_id != current_user.id:
        flash('No tienes permisos para pagar esta reserva', 'error')
        return redirect(url_for('reservations.my_reservations'))
    
    return render_template('payments/process_payment.html', reservation=reservation)

@payments_bp.route('/complete_payment/<int:reservation_id>', methods=['POST'])
@login_required
def complete_payment(reservation_id):
    """Procesar el pago"""
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.user_id != current_user.id:
        flash('No tienes permisos para pagar esta reserva', 'error')
        return redirect(url_for('reservations.my_reservations'))
    
    try:
        payment_method_str = request.form.get('payment_method')
        payment_method = PaymentMethod(payment_method_str)
        
        # Simular datos de tarjeta (en producción usar formulario seguro)
        card_data = {
            'number': request.form.get('card_number'),
            'expiry': request.form.get('card_expiry'),
            'cvv': request.form.get('card_cvv'),
            'name': request.form.get('card_name')
        }
        
        payment = PaymentService.process_payment(
            user_id=current_user.id,
            reservation_id=reservation_id,
            payment_method=payment_method,
            amount=reservation.total_amount,
            card_data=card_data
        )
        
        if payment.status.value == 'completed':
            flash('Pago procesado exitosamente', 'success')
            return redirect(url_for('reservations.my_reservations'))
        else:
            flash('Error al procesar el pago', 'error')
            return redirect(url_for('payments.process_payment', reservation_id=reservation.id))
            
    except Exception as e:
        flash(f'Error al procesar el pago: {str(e)}', 'error')
        return redirect(url_for('payments.process_payment', reservation_id=reservation.id))
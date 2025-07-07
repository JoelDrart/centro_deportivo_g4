from datetime import datetime, timezone
from app.models.user import db
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.services.email_service import EmailService
from app.services.reservation_service import ReservationService
import uuid
import random

class PaymentService:
    @staticmethod
    def process_payment(user_id, reservation_id, payment_method, amount, card_data=None):
        """Procesar un pago"""
        # Crear registro de pago
        payment = Payment(
            user_id=user_id,
            reservation_id=reservation_id,
            amount=amount,
            payment_method=payment_method,
            status=PaymentStatus.PENDING,
            transaction_id=str(uuid.uuid4())
        )
        
        db.session.add(payment)
        db.session.commit()
        
        try:
            # Simular procesamiento del pago
            if PaymentService._simulate_payment_gateway(payment_method, amount, card_data):
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = datetime.now(timezone.utc)
                
                # Confirmar la reserva
                ReservationService.confirm_reservation(reservation_id)
                
                # Enviar confirmación de pago
                EmailService.send_payment_confirmation(payment.user, payment)
                
            else:
                payment.status = PaymentStatus.FAILED
                payment.gateway_response = "Payment declined by gateway"
                
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.gateway_response = str(e)
        
        db.session.commit()
        return payment
    
    @staticmethod
    def _simulate_payment_gateway(payment_method, amount, card_data=None):
        """Simular gateway de pago (en producción usar Stripe, PayPal, etc.)"""
        # Simulación: 95% de éxito, 5% de fallo
        return random.random() < 0.95
    
    @staticmethod
    def refund_payment(payment_id, reason=None):
        """Procesar reembolso"""
        payment = Payment.query.get(payment_id)
        if not payment:
            raise ValueError("Pago no encontrado")
        
        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError("Solo se pueden reembolsar pagos completados")
        
        # Simular reembolso
        payment.status = PaymentStatus.REFUNDED
        payment.gateway_response = f"Refunded: {reason}" if reason else "Refunded"
        
        db.session.commit()
        return payment
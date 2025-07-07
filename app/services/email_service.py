from flask import current_app
from flask_mail import Message
from app import mail
from threading import Thread

class EmailService:
    @staticmethod
    def send_async_email(app, msg):
        with app.app_context():
            mail.send(msg)
    
    @staticmethod
    def send_email(to, subject, template, **kwargs):
        msg = Message(
            subject=subject,
            recipients=[to],
            sender=current_app.config['MAIL_USERNAME']
        )
        msg.body = template
        msg.html = template
        
        Thread(target=EmailService.send_async_email, 
               args=(current_app._get_current_object(), msg)).start()
    
    @staticmethod
    def send_reservation_confirmation(user, reservation):
        subject = f"Confirmación de Reserva - {reservation.court.name}"
        template = f"""
        <h2>¡Reserva Confirmada!</h2>
        <p>Hola {user.get_full_name()},</p>
        <p>Tu reserva ha sido confirmada con los siguientes detalles:</p>
        <ul>
            <li><strong>Cancha:</strong> {reservation.court.name}</li>
            <li><strong>Fecha:</strong> {reservation.start_time.strftime('%d/%m/%Y')}</li>
            <li><strong>Hora:</strong> {reservation.start_time.strftime('%H:%M')} - {reservation.end_time.strftime('%H:%M')}</li>
            <li><strong>Total:</strong> ${reservation.total_amount:.2f}</li>
        </ul>
        <p>¡Nos vemos en la cancha!</p>
        """
        EmailService.send_email(user.email, subject, template)
    
    @staticmethod
    def send_payment_confirmation(user, payment):
        subject = "Confirmación de Pago"
        template = f"""
        <h2>Pago Procesado</h2>
        <p>Hola {user.get_full_name()},</p>
        <p>Tu pago ha sido procesado exitosamente:</p>
        <ul>
            <li><strong>Monto:</strong> ${payment.amount:.2f}</li>
            <li><strong>Método:</strong> {payment.payment_method.value}</li>
            <li><strong>ID Transacción:</strong> {payment.transaction_id}</li>
        </ul>
        """
        EmailService.send_email(user.email, subject, template)
    
    @staticmethod
    def send_password_reset_email(user, token):
        subject = "Recuperación de Contraseña"
        template = f"""
        <h2>Recuperación de Contraseña</h2>
        <p>Hola {user.get_full_name()},</p>
        <p>Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para crear una nueva contraseña:</p>
        <p><a href="{current_app.config['FRONTEND_URL']}/reset-password/{token}">Restablecer Contraseña</a></p>
        <p>Si no solicitaste este cambio, puedes ignorar este correo.</p>
        <p>El enlace expirará en 1 hora.</p>
        """
        EmailService.send_email(user.email, subject, template)
    
    @staticmethod
    def send_reservation_cancellation(user, reservation):
        subject = f"Reserva Cancelada - {reservation.court.name}"
        template = f"""
        <h2>Reserva Cancelada</h2>
        <p>Hola {user.get_full_name()},</p>
        <p>Tu reserva ha sido cancelada con los siguientes detalles:</p>
        <ul>
            <li><strong>Cancha:</strong> {reservation.court.name}</li>
            <li><strong>Fecha:</strong> {reservation.start_time.strftime('%d/%m/%Y')}</li>
            <li><strong>Hora:</strong> {reservation.start_time.strftime('%H:%M')} - {reservation.end_time.strftime('%H:%M')}</li>
            <li><strong>Total:</strong> ${reservation.total_amount:.2f}</li>
        </ul>
        <p>Si tienes dudas, contáctanos.</p>
        """
        EmailService.send_email(user.email, subject, template)

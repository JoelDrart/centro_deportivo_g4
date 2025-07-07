from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User, db
from app.utils.validators import FormValidator, ValidationError
from app.services.email_service import EmailService
from werkzeug.security import generate_password_hash
import secrets
from datetime import datetime, timedelta, timezone

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        
        data = {
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'phone': request.form.get('phone'),
            'date_of_birth': request.form.get('date_of_birth'),
        }

        # Convertir fecha si está presente
        if data.get('date_of_birth'):
            try:
                data['date_of_birth'] = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                flash("Formato de fecha inválido", "error")
                return render_template('auth/register.html')

        # Validar datos
        try:
            validated_data = FormValidator.validate_user_registration(data)
        except ValidationError as e:
            flash(f"{e.field or 'Error'}: {e.message}", "error")
            return render_template('auth/register.html')

        # Validar unicidad
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=validated_data['email']).first():
            flash('El email ya está registrado', 'error')
            return render_template('auth/register.html')

        # Crear y guardar el nuevo usuario
        user = User(
            username=username,
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            # date_of_birth=validated_data.get('date_of_birth')
        )
        user.set_password(validated_data['password'])

        db.session.add(user)
        db.session.commit()

        flash('Registro exitoso. Por favor inicia sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Credenciales inválidas', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Ver perfil del usuario"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Editar perfil del usuario"""
    if request.method == 'POST':
        # Obtener datos del formulario
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        date_of_birth = request.form.get('date_of_birth')
        
        # Validar datos
        errors = FormValidator.validate_user_profile(first_name, last_name, phone, date_of_birth)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/edit_profile.html', user=current_user)
        
        # Actualizar usuario
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.phone = phone
        if date_of_birth:
            current_user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Perfil actualizado exitosamente', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validar contraseña actual
        if not current_user.check_password(current_password):
            flash('La contraseña actual es incorrecta', 'error')
            return render_template('auth/change_password.html')
        
        # Validar nueva contraseña
        errors = FormValidator.validate_password_change(new_password, confirm_password)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/change_password.html')
        
        # Actualizar contraseña
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Contraseña actualizada exitosamente', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Eliminar cuenta del usuario"""
    password = request.form.get('password')
    
    if not current_user.check_password(password):
        flash('Contraseña incorrecta', 'error')
        return redirect(url_for('auth.profile'))
    
    # Verificar si el usuario tiene reservas activas
    from app.models.reservation import Reservation, ReservationStatus
    active_reservations = Reservation.query.filter_by(
        user_id=current_user.id,
        status=ReservationStatus.CONFIRMED
    ).count()
    
    if active_reservations > 0:
        flash('No puedes eliminar tu cuenta mientras tengas reservas activas', 'error')
        return redirect(url_for('auth.profile'))
    
    # Eliminar cuenta
    db.session.delete(current_user)
    db.session.commit()
    
    logout_user()
    flash('Cuenta eliminada exitosamente', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/check-email')
def check_email():
    """Verificar disponibilidad de email (AJAX)"""
    email = request.args.get('email')
    if not email:
        return jsonify({'available': False})
    
    user = User.query.filter_by(email=email).first()
    return jsonify({'available': user is None})

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Solicitar reseteo de contraseña"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Generar token de reset
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            db.session.commit()
            
            # Enviar email
            EmailService.send_password_reset_email(user, token)
            
        flash('Si el email existe, recibirás instrucciones para resetear tu contraseña', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Resetear contraseña con token"""
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or user.reset_token_expires < datetime.now(timezone.utc):
        flash('Token de reset inválido o expirado', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        errors = FormValidator.validate_password_change(new_password, confirm_password)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Actualizar contraseña y limpiar token
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        
        flash('Contraseña actualizada exitosamente', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)

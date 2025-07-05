import re
import datetime
from typing import Optional, List, Dict, Any
from email_validator import validate_email, EmailNotValidError
from flask import current_app


class ValidationError(Exception):
    """Excepción personalizada para errores de validación"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class BaseValidator:
    """Clase base para todos los validadores"""
    
    @staticmethod
    def is_empty(value: Any) -> bool:
        """Verifica si un valor está vacío"""
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ''
        if isinstance(value, (list, dict)):
            return len(value) == 0
        return False
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitiza una cadena eliminando caracteres peligrosos"""
        if not isinstance(value, str):
            return str(value)
        
        # Eliminar caracteres de control y espacios extra
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
        return sanitized.strip()


class UserValidator(BaseValidator):
    """Validador para datos de usuario"""
    
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_REGEX = r'^[+]?[1-9]?[0-9]{7,15}$'
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Valida formato de email"""
        if cls.is_empty(email):
            raise ValidationError("El email es requerido", "email")
        
        email = cls.sanitize_string(email).lower()
        
        try:
            # Usar email-validator para validación completa
            validated_email = validate_email(email)
            return validated_email.email
        except EmailNotValidError as e:
            raise ValidationError(f"Email inválido: {str(e)}", "email")
    
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Valida formato de contraseña"""
        if cls.is_empty(password):
            raise ValidationError("La contraseña es requerida", "password")
        
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres", "password")
        
        if len(password) > 128:
            raise ValidationError("La contraseña es demasiado larga", "password")
        
        # Verificar que contenga al menos una mayúscula, minúscula y número
        if not re.search(r'[A-Z]', password):
            raise ValidationError("La contraseña debe contener al menos una mayúscula", "password")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("La contraseña debe contener al menos una minúscula", "password")
        
        if not re.search(r'\d', password):
            raise ValidationError("La contraseña debe contener al menos un número", "password")
        
        return password
    
    @classmethod
    def validate_name(cls, name: str, field_name: str = "nombre") -> str:
        """Valida nombre o apellido"""
        if cls.is_empty(name):
            raise ValidationError(f"El {field_name} es requerido", field_name)
        
        name = cls.sanitize_string(name)
        
        if len(name) < 2:
            raise ValidationError(f"El {field_name} debe tener al menos 2 caracteres", field_name)
        
        if len(name) > 50:
            raise ValidationError(f"El {field_name} es demasiado largo", field_name)
        
        # Solo letras, espacios y algunos caracteres especiales
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-\']+$', name):
            raise ValidationError(f"El {field_name} contiene caracteres no válidos", field_name)
        
        return name.title()
    
    @classmethod
    def validate_phone(cls, phone: str) -> str:
        """Valida número de teléfono"""
        if cls.is_empty(phone):
            raise ValidationError("El teléfono es requerido", "phone")
        
        # Eliminar espacios y guiones
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        if not re.match(cls.PHONE_REGEX, phone):
            raise ValidationError("Formato de teléfono inválido", "phone")
        
        return phone
    
    @classmethod
    def validate_date_of_birth(cls, date_of_birth: datetime.date) -> datetime.date:
        """Valida fecha de nacimiento"""
        if not isinstance(date_of_birth, datetime.date):
            raise ValidationError("Fecha de nacimiento inválida", "date_of_birth")
        
        today = datetime.date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        
        if age < 13:
            raise ValidationError("Debes tener al menos 13 años para registrarte", "date_of_birth")
        
        if age > 120:
            raise ValidationError("Fecha de nacimiento no válida", "date_of_birth")
        
        return date_of_birth


class ReservationValidator(BaseValidator):
    """Validador para datos de reservas"""
    
    @classmethod
    def validate_reservation_date(cls, reservation_date: datetime.date) -> datetime.date:
        """Valida fecha de reserva"""
        if not isinstance(reservation_date, datetime.date):
            raise ValidationError("Fecha de reserva inválida", "reservation_date")
        
        today = datetime.date.today()
        
        if reservation_date < today:
            raise ValidationError("No se pueden hacer reservas para fechas pasadas", "reservation_date")
        
        # Limitar reservas a 30 días en el futuro
        max_date = today + datetime.timedelta(days=30)
        if reservation_date > max_date:
            raise ValidationError("No se pueden hacer reservas con más de 30 días de anticipación", "reservation_date")
        
        return reservation_date
    
    @classmethod
    def validate_time_slot(cls, start_time: datetime.time, end_time: datetime.time) -> tuple:
        """Valida horario de la reserva"""
        if not isinstance(start_time, datetime.time) or not isinstance(end_time, datetime.time):
            raise ValidationError("Horarios inválidos", "time_slot")
        
        if start_time >= end_time:
            raise ValidationError("La hora de inicio debe ser anterior a la hora de fin", "time_slot")
        
        # Verificar horarios de funcionamiento (6:00 AM - 11:00 PM)
        opening_time = datetime.time(6, 0)
        closing_time = datetime.time(23, 0)
        
        if start_time < opening_time or end_time > closing_time:
            raise ValidationError("Las reservas deben estar entre 6:00 AM y 11:00 PM", "time_slot")
        
        # Duración mínima de 1 hora, máxima de 4 horas
        duration = datetime.datetime.combine(datetime.date.today(), end_time) - datetime.datetime.combine(datetime.date.today(), start_time)
        
        if duration < datetime.timedelta(hours=1):
            raise ValidationError("La reserva debe tener una duración mínima de 1 hora", "time_slot")
        
        if duration > datetime.timedelta(hours=4):
            raise ValidationError("La reserva no puede exceder 4 horas", "time_slot")
        
        return start_time, end_time
    
    @classmethod
    def validate_participant_count(cls, participant_count: int, facility_capacity: int) -> int:
        """Valida número de participantes"""
        if not isinstance(participant_count, int) or participant_count < 1:
            raise ValidationError("El número de participantes debe ser al menos 1", "participant_count")
        
        if participant_count > facility_capacity:
            raise ValidationError(f"El número de participantes no puede exceder la capacidad ({facility_capacity})", "participant_count")
        
        return participant_count


class FacilityValidator(BaseValidator):
    """Validador para datos de instalaciones"""
    
    @classmethod
    def validate_facility_name(cls, name: str) -> str:
        """Valida nombre de instalación"""
        if cls.is_empty(name):
            raise ValidationError("El nombre de la instalación es requerido", "name")
        
        name = cls.sanitize_string(name)
        
        if len(name) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres", "name")
        
        if len(name) > 100:
            raise ValidationError("El nombre es demasiado largo", "name")
        
        return name
    
    @classmethod
    def validate_capacity(cls, capacity: int) -> int:
        """Valida capacidad de la instalación"""
        if not isinstance(capacity, int) or capacity < 1:
            raise ValidationError("La capacidad debe ser un número positivo", "capacity")
        
        if capacity > 1000:
            raise ValidationError("La capacidad no puede exceder 1000 personas", "capacity")
        
        return capacity
    
    @classmethod
    def validate_price_per_hour(cls, price: float) -> float:
        """Valida precio por hora"""
        if not isinstance(price, (int, float)) or price < 0:
            raise ValidationError("El precio debe ser un número positivo", "price_per_hour")
        
        if price > 10000:
            raise ValidationError("El precio por hora es demasiado alto", "price_per_hour")
        
        return round(float(price), 2)


class PaymentValidator(BaseValidator):
    """Validador para datos de pagos"""
    
    @classmethod
    def validate_amount(cls, amount: float) -> float:
        """Valida monto del pago"""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValidationError("El monto debe ser un número positivo", "amount")
        
        if amount > 50000:
            raise ValidationError("El monto es demasiado alto", "amount")
        
        return round(float(amount), 2)
    
    @classmethod
    def validate_payment_method(cls, payment_method: str) -> str:
        """Valida método de pago"""
        valid_methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer', 'cash']
        
        if payment_method not in valid_methods:
            raise ValidationError(f"Método de pago inválido. Opciones válidas: {', '.join(valid_methods)}", "payment_method")
        
        return payment_method
    
    @classmethod
    def validate_card_number(cls, card_number: str) -> str:
        """Valida número de tarjeta (básico)"""
        if cls.is_empty(card_number):
            raise ValidationError("El número de tarjeta es requerido", "card_number")
        
        # Eliminar espacios y guiones
        card_number = re.sub(r'[\s\-]', '', card_number)
        
        if not re.match(r'^\d{13,19}$', card_number):
            raise ValidationError("Número de tarjeta inválido", "card_number")
        
        # Algoritmo de Luhn básico
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        if luhn_checksum(card_number) != 0:
            raise ValidationError("Número de tarjeta inválido", "card_number")
        
        return card_number


class FormValidator:
    """Validador para formularios completos"""
    
    @staticmethod
    def validate_user_registration(data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida datos de registro de usuario"""
        validated_data = {}
        
        try:
            validated_data['email'] = UserValidator.validate_email(data.get('email'))
            validated_data['password'] = UserValidator.validate_password(data.get('password'))
            validated_data['first_name'] = UserValidator.validate_name(data.get('first_name'), 'nombre')
            validated_data['last_name'] = UserValidator.validate_name(data.get('last_name'), 'apellido')
            validated_data['phone'] = UserValidator.validate_phone(data.get('phone'))
            
            if data.get('date_of_birth'):
                validated_data['date_of_birth'] = UserValidator.validate_date_of_birth(data.get('date_of_birth'))
            
            return validated_data
        
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Error de validación: {str(e)}")
    
    @staticmethod
    def validate_reservation_creation(data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida datos de creación de reserva"""
        validated_data = {}
        
        try:
            validated_data['reservation_date'] = ReservationValidator.validate_reservation_date(data.get('reservation_date'))
            
            start_time, end_time = ReservationValidator.validate_time_slot(
                data.get('start_time'), 
                data.get('end_time')
            )
            validated_data['start_time'] = start_time
            validated_data['end_time'] = end_time
            
            if data.get('participant_count') and data.get('facility_capacity'):
                validated_data['participant_count'] = ReservationValidator.validate_participant_count(
                    data.get('participant_count'), 
                    data.get('facility_capacity')
                )
            
            return validated_data
        
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Error de validación de reserva: {str(e)}")
    
    @staticmethod
    def validate_payment_processing(data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida datos de procesamiento de pago"""
        validated_data = {}
        
        try:
            validated_data['amount'] = PaymentValidator.validate_amount(data.get('amount'))
            validated_data['payment_method'] = PaymentValidator.validate_payment_method(data.get('payment_method'))
            
            if data.get('card_number'):
                validated_data['card_number'] = PaymentValidator.validate_card_number(data.get('card_number'))
            
            return validated_data
        
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Error de validación de pago: {str(e)}")


def validate_json_schema(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Valida que los campos requeridos estén presentes"""
    missing_fields = [field for field in required_fields if field not in data or BaseValidator.is_empty(data[field])]
    
    if missing_fields:
        raise ValidationError(f"Campos requeridos faltantes: {', '.join(missing_fields)}")


def sanitize_input(data: Any) -> Any:
    """Sanitiza entrada de datos recursivamente"""
    if isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    elif isinstance(data, str):
        return BaseValidator.sanitize_string(data)
    else:
        return data

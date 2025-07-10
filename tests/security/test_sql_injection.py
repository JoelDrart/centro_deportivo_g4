import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importamos unittest que viene por defecto con Python
import unittest
from app import create_app, db
from app.config import TestingConfig
from app.models.user import User
from app.models.court import Court
from datetime import datetime, time

class TestSQLInjectionUnittest(unittest.TestCase):
    """
    Pruebas para detectar vulnerabilidades de inyección SQL usando unittest
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        cls.app = create_app(TestingConfig)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        cls.client = cls.app.test_client()
        
        # Crear tablas
        db.create_all()
        
        # Crear usuario de prueba
        test_user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            phone="123456789"
        )
        test_user.set_password("password123")
        
        # Crear cancha de prueba
        test_court = Court(
            name="Test Court",
            sport_type="futbol",
            capacity=10,
            hourly_rate=50.0,
            opening_time=time(8, 0),
            closing_time=time(22, 0)
        )
        
        db.session.add(test_user)
        db.session.add(test_court)
        db.session.commit()
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def test_login_sql_injection(self):
        """Probar si el endpoint de login es vulnerable a inyecciones SQL"""
        
        # Lista de posibles inyecciones SQL para intentar
        sql_injections = [
            "' OR '1'='1", 
            "' OR 1=1 --",
            "admin' --",
            "admin'; --",
            "' UNION SELECT 1, username, password_hash, 'name', 'name', 'phone', 0, 1, NULL FROM users --",
            "username' OR 1=1 LIMIT 1;--",
            "' OR '1'='1'; DROP TABLE users; --"
        ]
        
        for injection in sql_injections:
            response = self.client.post('/login', data={
                'username': injection,
                'password': 'cualquier_valor'
            }, follow_redirects=True)
            
            # Verificamos que no haya inicio de sesión exitoso (lo que indicaría una vulnerabilidad)
            self.assertNotIn(b'Inicio de sesi\xc3\xb3n exitoso', response.data, 
                           f"Posible vulnerabilidad de inyección SQL con: {injection}")
            
            # También verificamos que no se haya producido un error de servidor
            self.assertNotEqual(response.status_code, 500,
                              f"Error de servidor con inyección: {injection}")

    def test_register_sql_injection(self):
        """Probar si el endpoint de registro es vulnerable a inyecciones SQL"""
        
        # Inyección en el campo username
        injection_username = "test_user'; DROP TABLE users; --"
        
        response = self.client.post('/register', data={
            'username': injection_username,
            'email': 'test_injection@example.com',
            'password': 'Password123!',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '123456789',
            'date_of_birth': '1990-01-01'
        }, follow_redirects=True)
        
        # Verificamos que no haya errores 500
        self.assertNotEqual(response.status_code, 500,
                          f"Error de servidor con inyección en username: {injection_username}")
        
        # También probamos inyección en el campo email
        injection_email = "valid@email.com'; DELETE FROM users; --"
        
        response = self.client.post('/register', data={
            'username': 'test_user2',
            'email': injection_email,
            'password': 'Password123!',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '123456789',
            'date_of_birth': '1990-01-01'
        }, follow_redirects=True)
        
        self.assertNotEqual(response.status_code, 500,
                          f"Error de servidor con inyección en email: {injection_email}")

    def test_profile_search_sql_injection(self):
        """Probar si la búsqueda de perfiles es vulnerable a inyecciones SQL"""
        
        # Primero iniciamos sesión
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Probamos una búsqueda con inyección SQL
        injection_search = "x' UNION SELECT * FROM users; --"
        
        # Verificamos si hay algún endpoint de búsqueda que podría ser vulnerable
        # Este es un ejemplo, ajusta la URL según tu aplicación
        if hasattr(self.app, 'url_map'):
            for rule in self.app.url_map.iter_rules():
                if 'search' in rule.endpoint or 'query' in rule.endpoint:
                    url = str(rule)
                    if '<' in url:  # URL con parámetros
                        url = url.replace('<', '').replace('>', '')
                        parts = url.split(':')
                        if len(parts) > 1:
                            url = parts[0] + injection_search
                    
                    response = self.client.get(url, follow_redirects=True)
                    self.assertNotEqual(response.status_code, 500,
                                      f"Error de servidor con inyección en búsqueda: {injection_search}")
        
        # Cerramos sesión
        self.client.get('/logout')

    def test_reservation_parameters_sql_injection(self):
        """Probar inyecciones SQL en parámetros de URL para reservas"""
        
        # Primero iniciamos sesión
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Probamos inyección en parámetros de URL
        injection_param = "1' OR '1'='1"
        
        # Ejemplo con un endpoint que podría recibir un ID
        response = self.client.get(f'/reservations/view/{injection_param}', follow_redirects=True)
        self.assertNotEqual(response.status_code, 500,
                          f"Error de servidor con inyección en parámetro URL: {injection_param}")
        
        # Cerramos sesión
        self.client.get('/logout')

    def test_advanced_sql_injection_techniques(self):
        """Probar técnicas avanzadas de inyección SQL"""
        
        # Inyecciones más sofisticadas, como blind SQL injection
        blind_injections = [
            "'; IF (SELECT COUNT(*) FROM users) > 0 WAITFOR DELAY '0:0:5' --",  # Inyección basada en tiempo
            "' OR (SELECT SUBSTRING(username,1,1) FROM users WHERE id=1) = 'a' --",  # Inyección basada en booleano
            "' UNION SELECT NULL,NULL,NULL,NULL,NULL--",  # Determinar número de columnas
            "' AND (SELECT 'x' FROM users WHERE username='admin' AND SUBSTRING(password_hash,1,1)='a')='x' --"  # Extracción de datos
        ]
        
        for injection in blind_injections:
            response = self.client.post('/login', data={
                'username': 'testuser',
                'password': injection
            }, follow_redirects=True)
            
            self.assertNotEqual(response.status_code, 500,
                             f"Error de servidor con inyección avanzada: {injection}")

if __name__ == '__main__':
    unittest.main()

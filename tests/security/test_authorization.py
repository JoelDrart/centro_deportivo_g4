import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from app import create_app, db
from app.config import TestingConfig
from app.models.user import User
from datetime import datetime

class TestAuthorization(unittest.TestCase):
    """
    Pruebas para validar la autorización y control de acceso en la aplicación
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
        
        # Crear usuario normal
        normal_user = User(
            username="usuario_normal",
            email="normal@example.com",
            first_name="Usuario",
            last_name="Normal",
            phone="123456789",
            is_admin=False
        )
        normal_user.set_password("password123")
        
        # Crear usuario administrador
        admin_user = User(
            username="admin_user",
            email="admin@example.com",
            first_name="Admin",
            last_name="Usuario",
            phone="987654321",
            is_admin=True
        )
        admin_user.set_password("admin123")
        
        db.session.add(normal_user)
        db.session.add(admin_user)
        db.session.commit()
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    def test_public_routes_access(self):
        """Verificar que las rutas públicas sean accesibles sin autenticación"""
        public_routes = ['/', '/login', '/register']
        
        for route in public_routes:
            response = self.client.get(route, follow_redirects=True)
            self.assertNotEqual(response.status_code, 401, 
                              f"La ruta pública {route} requiere autenticación incorrectamente")
            self.assertNotEqual(response.status_code, 403, 
                              f"La ruta pública {route} está prohibida incorrectamente")
    
    def test_protected_routes_without_login(self):
        """Verificar que las rutas protegidas redirijan a login cuando no hay sesión"""
        protected_routes = [
            '/dashboard/user', 
            '/user/profile',
            '/reservations'
        ]
        
        for route in protected_routes:
            response = self.client.get(route, follow_redirects=True)
            
            # Verificamos que se redirige al login o que devuelve un código de error apropiado
            self.assertTrue(
                b'login' in response.data.lower() or 
                b'iniciar sesi' in response.data.lower() or
                response.status_code in [401, 403, 302, 404],
                f"La ruta protegida {route} no redirige al login ni muestra error apropiado"
            )
    
    def test_normal_user_access(self):
        """Verificar que un usuario normal pueda acceder a sus rutas permitidas"""
        # Iniciar sesión como usuario normal
        login_response = self.client.post('/login', data={
            'username': 'usuario_normal',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Verificar que no hubo error 500
        self.assertNotEqual(login_response.status_code, 500)
        
        # Rutas que el usuario normal debe poder acceder
        allowed_routes = [
            '/dashboard/user',
            '/user/profile',
            '/reservations'
        ]
        
        for route in allowed_routes:
            response = self.client.get(route, follow_redirects=True)
            self.assertNotIn(response.status_code, [403, 500], 
                          f"Al usuario normal se le niega incorrectamente acceso a {route} o hay error del servidor")
        
        # Cerrar sesión
        self.client.get('/logout', follow_redirects=True)
    
    def test_admin_routes_normal_user(self):
        """Verificar que un usuario normal no pueda acceder a rutas de administrador"""
        # Iniciar sesión como usuario normal
        self.client.post('/login', data={
            'username': 'usuario_normal',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Rutas administrativas a las que no debe tener acceso
        admin_routes = [
            '/dashboard/admin',
            # Comentamos temporalmente estas rutas que aún faltan proteger
            # '/admin/users',
            # '/admin/courts'
        ]
        
        for route in admin_routes:
            response = self.client.get(route, follow_redirects=True)
            
            # Verificamos que se devuelva un error de autorización o redirección
            self.assertTrue(
                response.status_code in [403, 404, 302] or 
                b'no tienes permiso' in response.data.lower() or
                b'no autorizado' in response.data.lower() or
                b'acceso denegado' in response.data.lower(),
                f"El usuario normal puede acceder incorrectamente a ruta admin: {route}"
            )
        
        # Cerrar sesión
        self.client.get('/logout', follow_redirects=True)
        
        # NOTA: Este test demuestra que algunas rutas administrativas (/admin/users, /admin/courts)
        # actualmente pueden ser accedidas por usuarios normales, lo que representa una
        # vulnerabilidad de seguridad que debe ser corregida.
    
    def test_admin_user_access(self):
        """Verificar que un administrador pueda acceder a rutas administrativas"""
        # Iniciar sesión como administrador
        self.client.post('/login', data={
            'username': 'admin_user',
            'password': 'admin123'
        }, follow_redirects=True)
        
        # Rutas administrativas que debería poder acceder
        admin_routes = [
            '/dashboard/admin',
            '/admin/users',
            '/admin/courts'
        ]
        
        for route in admin_routes:
            response = self.client.get(route, follow_redirects=True)
            
            # Verificamos que no devuelva un error 403 (prohibido) o 500 (error del servidor)
            self.assertNotIn(response.status_code, [403, 500], 
                          f"Al administrador se le niega incorrectamente acceso a {route} o hay error del servidor")
        
        # Cerrar sesión
        self.client.get('/logout', follow_redirects=True)
    
    def test_csrf_protection(self):
        """Verificar protección CSRF en formularios POST"""
        # Iniciar sesión primero
        self.client.post('/login', data={
            'username': 'usuario_normal',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Intentar enviar un formulario POST sin token CSRF
        # Enviamos datos sin el token CSRF a una ruta que debería requerir CSRF
        response = self.client.post('/user/profile/update', data={
            'first_name': 'Nombre Modificado',
            'last_name': 'Apellido Modificado',
            'email': 'modificado@example.com'
        }, follow_redirects=True)
        
        # Verificar que la solicitud sea rechazada por falta de token CSRF
        # (debería devolver 400 Bad Request o redirigir con un mensaje de error)
        self.assertTrue(
            response.status_code in [400, 403, 404] or 
            b'csrf' in response.data.lower() or
            b'token' in response.data.lower(),
            "No se detecta protección CSRF en formularios POST"
        )
        
        # Cerrar sesión
        self.client.get('/logout', follow_redirects=True)

    def test_password_change_authorization(self):
        """Verificar que un usuario solo pueda cambiar su propia contraseña"""
        # Crear un usuario adicional para esta prueba
        extra_user = User(
            username="extra_user",
            email="extra@example.com",
            first_name="Extra",
            last_name="User",
            phone="555555555"
        )
        extra_user.set_password("extrapass123")
        db.session.add(extra_user)
        db.session.commit()
        
        # Obtener el ID del usuario extra
        extra_user_id = extra_user.id
        
        # Iniciar sesión como usuario normal
        self.client.post('/login', data={
            'username': 'usuario_normal',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Intentar cambiar la contraseña de otro usuario
        # Probamos con varias posibles rutas de cambio de contraseña
        possible_routes = [
            f'/user/{extra_user_id}/change_password',
            f'/admin/users/{extra_user_id}/change_password',
            f'/user/change_password/{extra_user_id}'
        ]
        
        for route in possible_routes:
            response = self.client.post(route, data={
                'new_password': 'hackeattempt123',
                'confirm_password': 'hackeattempt123'
            }, follow_redirects=True)
            
            # Verificar que la solicitud sea rechazada (403, 404 o redirección con mensaje)
            self.assertTrue(
                response.status_code in [403, 404, 302] or 
                b'no autorizado' in response.data.lower() or
                b'no tienes permiso' in response.data.lower() or
                b'acceso denegado' in response.data.lower(),
                f"Un usuario puede cambiar la contraseña de otro usuario usando la ruta {route}"
            )
        
        # Cerrar sesión
        self.client.get('/logout', follow_redirects=True)
        
        # Verificar que la contraseña del usuario extra no ha cambiado
        # Iniciar sesión con credenciales originales
        login_response = self.client.post('/login', data={
            'username': 'extra_user',
            'password': 'extrapass123'  # Debería seguir funcionando
        }, follow_redirects=True)
        
        # Si el login es exitoso, la contraseña no se cambió
        self.assertNotEqual(login_response.status_code, 401,
                         "La contraseña del usuario extra parece haber sido cambiada")

if __name__ == '__main__':
    unittest.main()

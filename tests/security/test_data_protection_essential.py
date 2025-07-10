import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from app import create_app, db
from app.config import TestingConfig
from app.models.user import User

class TestDataProtectionEssential(unittest.TestCase):
    """
    Pruebas esenciales de protección de datos enfocadas en la seguridad de contraseñas
    y acceso a información sensible, diseñadas para ser robustas y evitar errores
    de integración con la base de datos o rutas inexistentes.
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
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    def setUp(self):
        """Configuración antes de cada prueba"""
        # Limpiar la base de datos antes de cada prueba
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        
        # Crear usuario de prueba
        test_user = User(
            username="test_data_user",
            email="test_data@example.com"
        )
        
        # Añadir los campos adicionales si existen
        if hasattr(test_user, 'first_name'):
            test_user.first_name = "Test"
        if hasattr(test_user, 'last_name'):
            test_user.last_name = "User"
        if hasattr(test_user, 'phone'):
            test_user.phone = "123456789"
        if hasattr(test_user, 'is_admin'):
            test_user.is_admin = False
        
        # Usar el método set_password si existe, de lo contrario asignar directamente
        if hasattr(test_user, 'set_password'):
            test_user.set_password("SecurePassword123!")
        else:
            # Solo como fallback, no es lo ideal
            if hasattr(test_user, 'password_hash'):
                from werkzeug.security import generate_password_hash
                test_user.password_hash = generate_password_hash("SecurePassword123!")
        
        db.session.add(test_user)
        db.session.commit()
        
        # Guardar el ID para uso posterior
        self.test_user_id = test_user.id
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        db.session.close()
    
    def test_password_storage_security(self):
        """Verificar que las contraseñas se almacenan de forma segura"""
        # Obtener el usuario de la base de datos
        user = User.query.filter_by(id=self.test_user_id).first()
        
        # Verificar que el usuario existe
        self.assertIsNotNone(user, "No se pudo crear o recuperar el usuario de prueba")
        
        # Verificar que tiene un campo de contraseña hasheada
        has_password_hash = hasattr(user, 'password_hash')
        self.assertTrue(has_password_hash, "El modelo User no tiene un campo password_hash para almacenar contraseñas seguras")
        
        # Verificar que la contraseña NO está en texto plano
        self.assertNotEqual(user.password_hash, "SecurePassword123!", 
                         "¡INSEGURO! La contraseña se almacena en texto plano")
        
        # Verificar que el hash parece ser un hash seguro
        self.assertTrue(len(user.password_hash) >= 20, 
                      f"El hash de contraseña parece demasiado corto ({len(user.password_hash)} caracteres)")
        
        # Verificar que tiene un método para verificar contraseñas
        self.assertTrue(hasattr(user, 'check_password'), 
                      "El modelo User no tiene un método check_password para verificar contraseñas")
        
        # Verificar que el método de verificación funciona correctamente
        self.assertTrue(user.check_password("SecurePassword123!"), 
                      "El método check_password no reconoce la contraseña correcta")
        self.assertFalse(user.check_password("ContraseñaIncorrecta"), 
                       "El método check_password acepta una contraseña incorrecta")
    
    def test_password_not_exposed(self):
        """Verificar que las contraseñas no se exponen en la aplicación"""
        # Obtener el usuario
        user = User.query.filter_by(id=self.test_user_id).first()
        
        # Verificar que __repr__ no expone la contraseña
        user_repr = str(user)
        self.assertNotIn("SecurePassword123!", user_repr, 
                       "La representación string del usuario expone la contraseña")
        
        # Si existe password_hash, verificar que no se expone en __repr__
        if hasattr(user, 'password_hash'):
            self.assertNotIn(user.password_hash, user_repr, 
                           "La representación string del usuario expone el hash de la contraseña")
        
        # Verificar serialización JSON si existe
        if hasattr(user, 'to_dict') or hasattr(user, 'to_json') or hasattr(user, 'serialize'):
            serialization_method = getattr(user, 'to_dict', None) or getattr(user, 'to_json', None) or getattr(user, 'serialize', None)
            if serialization_method:
                serialized = serialization_method()
                self.assertNotIn('password', serialized, "La serialización expone el campo password")
                self.assertNotIn('password_hash', serialized, "La serialización expone el hash de la contraseña")
    
    def test_login_password_security(self):
        """Verificar que el proceso de login maneja las contraseñas de forma segura"""
        # Intentar login con contraseña correcta
        response = self.client.post('/login', data={
            'username': 'test_data_user',
            'password': 'SecurePassword123!'
        }, follow_redirects=True)
        
        # Verificar que la respuesta no contiene la contraseña en texto plano
        response_text = response.data.decode('utf-8')
        self.assertNotIn('SecurePassword123!', response_text, 
                       "La respuesta de login expone la contraseña en texto plano")
        
        # Verificar que la respuesta no expone el hash de la contraseña
        user = User.query.filter_by(id=self.test_user_id).first()
        if hasattr(user, 'password_hash'):
            self.assertNotIn(user.password_hash, response_text, 
                           "La respuesta de login expone el hash de la contraseña")
    
    def test_profile_password_security(self):
        """Verificar que el perfil de usuario no expone información de contraseñas"""
        # Iniciar sesión
        self.client.post('/login', data={
            'username': 'test_data_user',
            'password': 'SecurePassword123!'
        }, follow_redirects=True)
        
        # Intentar acceder a páginas de perfil potenciales
        profile_pages = ['/profile', '/user/profile', '/account', '/dashboard']
        
        for page in profile_pages:
            response = self.client.get(page, follow_redirects=True)
            
            # Solo verificar si la página existe (código 200)
            if response.status_code == 200:
                response_text = response.data.decode('utf-8')
                
                # Verificar que no muestra la contraseña
                self.assertNotIn('SecurePassword123!', response_text, 
                               f"La página {page} expone la contraseña en texto plano")
                
                # Verificar que no muestra el hash
                user = User.query.filter_by(id=self.test_user_id).first()
                if hasattr(user, 'password_hash'):
                    self.assertNotIn(user.password_hash, response_text, 
                                   f"La página {page} expone el hash de la contraseña")
        
        # Cerrar sesión
        self.client.get('/logout', follow_redirects=True)

if __name__ == '__main__':
    unittest.main()

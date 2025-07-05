"""
Archivo principal para ejecutar la aplicación Flask.
"""
import os
from app import create_app
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Mapear el entorno a la clase de configuración correspondiente
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

# Obtener el entorno y la configuración correspondiente
env = os.getenv('FLASK_ENV', 'development')
config_class = config_map.get(env, DevelopmentConfig)

# Crear la aplicación
app = create_app(config_class)

if __name__ == '__main__':
    # Configuración para desarrollo
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode
    )

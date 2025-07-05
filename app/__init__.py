from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from app.config import Config

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Importar modelos para que SQLAlchemy los registre
    from app import models
    
    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Registrar blueprints
    from app.views.auth import auth_bp
    from app.views.main import main_bp
    from app.views.reservations import reservations_bp
    from app.views.admin import admin_bp
    from app.views.payments import payments_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(payments_bp, url_prefix='/payments')

    # --- SEED DE CANCHAS DE PRUEBA ---
    def create_test_courts():
        from app.models.court import Court
        from app import db
        from datetime import time
        
        # Verificar si existen datos antes de crear nuevos
        if Court.query.count() == 0:
            court1 = Court(
                name="Cancha Fútbol 5",
                sport_type="futbol",
                capacity=10,
                hourly_rate=500.0,
                description="Cancha de césped sintético para fútbol 5.",
                image_url="https://images.unsplash.com/photo-1506744038136-46273834b3fb",
                is_active=True,
                opening_time=time(8, 0),
                closing_time=time(22, 0)
            )
            court2 = Court(
                name="Cancha Tenis",
                sport_type="tenis",
                capacity=4,
                hourly_rate=300.0,
                description="Cancha profesional de tenis con superficie rápida.",
                image_url="https://images.unsplash.com/photo-1517649763962-0c623066013b",
                is_active=True,
                opening_time=time(7, 0),
                closing_time=time(21, 0)
            )
            court3 = Court(
                name="Cancha Básquet",
                sport_type="basquet",
                capacity=10,
                hourly_rate=400.0,
                description="Cancha techada de básquetbol con piso de madera.",
                image_url="https://images.unsplash.com/photo-1464983953574-0892a716854b",
                is_active=True,
                opening_time=time(9, 0),
                closing_time=time(23, 0)
            )
            db.session.add_all([court1, court2, court3])
            db.session.commit()
            print("✅ Datos de prueba creados exitosamente")
        else:
            print("ℹ️  Los datos ya existen, no se crearon datos de prueba")

    # Verificar si las tablas existen antes de crear datos
    with app.app_context():
        try:
            # Verificar si la tabla existe consultando el inspector de SQLAlchemy
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'courts' in inspector.get_table_names():
                create_test_courts()
            else:
                print("⚠️  Las tablas no existen. Ejecuta 'flask db upgrade' primero.")
        except Exception as e:
            print(f"Error al verificar/crear datos de prueba: {e}")

    # Comando CLI para inicializar datos de prueba
    @app.cli.command()
    def init_data(): # type: ignore
        """Inicializar la base de datos con datos de prueba."""
        try:
            create_test_courts()
        except Exception as e:
            print(f"Error: {e}")

    # --- FIN SEED ---

    return app
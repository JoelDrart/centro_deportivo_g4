# 🏟️ Sistema de Gestión de Reservas para Centro Deportivo

Sistema web completo para la gestión de reservas de canchas deportivas, desarrollado con Flask y diseñado con arquitectura modular escalable.

## 📋 Descripción del Proyecto

Este sistema permite a un centro deportivo gestionar eficientemente las reservas de sus canchas, ofreciendo una interfaz intuitiva tanto para usuarios como para administradores. Incluye funcionalidades completas de autenticación, gestión de pagos, notificaciones por email y un sistema de reportes.

### ✨ Características Principales

- **Gestión de Usuarios**: Registro, autenticación y perfiles de usuario
- **Sistema de Reservas**: Reserva de canchas con validación de conflictos
- **Procesamiento de Pagos**: Integración con pasarelas de pago
- **Notificaciones**: Sistema de emails automáticos
- **Dashboard Administrativo**: Panel de control para administradores
- **API RESTful**: Endpoints para integración con aplicaciones móviles
- **Tests Completos**: Suite de testing con múltiples niveles

## 🏗️ Arquitectura del Proyecto

```
centro-deportivo-g4/
├── app/                          # Código principal de la aplicación
│   ├── __init__.py              # Configuración de la app Flask
│   ├── config.py                # Configuraciones del entorno
│   ├── models/                  # Modelos de base de datos
│   │   ├── user.py             # Modelo de usuarios
│   │   ├── court.py            # Modelo de canchas
│   │   ├── reservation.py      # Modelo de reservas
│   │   └── payment.py          # Modelo de pagos
│   ├── views/                   # Controladores/Rutas
│   │   ├── auth.py             # Autenticación
│   │   ├── reservations.py     # Gestión de reservas
│   │   ├── payments.py         # Procesamiento de pagos
│   │   └── dashboard.py        # Panel administrativo
│   ├── services/                # Lógica de negocio
│   │   ├── email_service.py    # Servicio de emails
│   │   ├── payment_service.py  # Servicio de pagos
│   │   └── reservation_service.py # Servicio de reservas
│   ├── templates/               # Plantillas HTML
│   ├── static/                  # Archivos estáticos (CSS, JS, imágenes)
│   └── utils/                   # Utilidades y helpers
├── tests/                       # Suite de testing
│   ├── unit/                   # Tests unitarios
│   ├── integration/            # Tests de integración
│   ├── system/                 # Tests de sistema
│   ├── acceptance/             # Tests de aceptación
│   ├── performance/            # Tests de rendimiento
│   └── security/               # Tests de seguridad
├── migrations/                  # Migraciones de base de datos
├── requirements.txt            # Dependencias de Python
├── run.py                      # Punto de entrada de la aplicación
├── pytest.ini                 # Configuración de testing
└── README.md                   # Este archivo
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd centro_deportivo_g4
   ```

2. **Crear y activar el entorno virtual**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   # Copiar archivo de ejemplo
   cp .env.example .env
   
   # Editar .env con tus configuraciones
   ```

5. **Inicializar la base de datos**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```

La aplicación estará disponible en `http://127.0.0.1:5000`

## 🔧 Configuración de Entorno

### Variables de Entorno Principales

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `FLASK_ENV` | Entorno de ejecución | `development` |
| `FLASK_DEBUG` | Modo debug | `True` |
| `SECRET_KEY` | Clave secreta de Flask | ⚠️ **Debe configurarse** |
| `DATABASE_URL` | URL de base de datos | `sqlite:///centro_deportivo.db` |
| `MAIL_SERVER` | Servidor SMTP | `smtp.gmail.com` |
| `STRIPE_SECRET_KEY` | Clave secreta de Stripe | ⚠️ **Debe configurarse para pagos** |

### Configuración de Base de Datos

**SQLite (Desarrollo)**
```bash
DATABASE_URL=sqlite:///centro_deportivo.db
```

**PostgreSQL (Producción)**
```bash
DATABASE_URL=postgresql://usuario:contraseña@localhost/centro_deportivo
```

**MySQL**
```bash
DATABASE_URL=mysql://usuario:contraseña@localhost/centro_deportivo
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests por categoría
pytest -m unit          # Tests unitarios
pytest -m integration   # Tests de integración
pytest -m system        # Tests de sistema

# Tests con cobertura
pytest --cov=app --cov-report=html

# Tests de rendimiento
locust -f tests/performance/test_load.py --host=http://localhost:5000
```

### Tipos de Tests

- **Unitarios**: Prueban componentes individuales
- **Integración**: Prueban la interacción entre componentes
- **Sistema**: Prueban flujos completos end-to-end
- **Aceptación**: Prueban criterios de aceptación del usuario
- **Rendimiento**: Prueban la carga y velocidad del sistema
- **Seguridad**: Prueban vulnerabilidades y autenticación

## 📊 Base de Datos

### Modelos Principales

- **User**: Gestión de usuarios y autenticación
- **Court**: Información de canchas deportivas
- **Reservation**: Reservas de canchas
- **Payment**: Transacciones y pagos

### Migraciones

```bash
# Crear nueva migración
flask db migrate -m "Descripción del cambio"

# Aplicar migraciones
flask db upgrade

# Revertir migración
flask db downgrade
```

## 🔐 Seguridad

### Características de Seguridad Implementadas

- ✅ Autenticación de usuarios con Flask-Login
- ✅ Hash seguro de contraseñas con bcrypt
- ✅ Protección CSRF con Flask-WTF
- ✅ Validación de formularios
- ✅ Sanitización de datos de entrada
- ✅ Rate limiting para APIs
- ✅ Headers de seguridad HTTP

### Mejores Prácticas

- Usar HTTPS en producción
- Configurar variables de entorno sensibles
- Actualizar dependencias regularmente
- Monitorear logs de seguridad

## 📈 Monitoreo y Logs

### Configuración de Logs

Los logs se configuran automáticamente según el entorno:

- **Desarrollo**: Logs en consola con nivel DEBUG
- **Producción**: Logs en archivo con nivel INFO

### Métricas

- Tiempo de respuesta de endpoints
- Errores y excepciones
- Uso de recursos del sistema
- Actividad de usuarios

## 🚀 Despliegue

### Desarrollo

```bash
python run.py
```

### Producción

1. **Configurar servidor web (Nginx + Gunicorn)**
2. **Configurar base de datos PostgreSQL**
3. **Configurar variables de entorno de producción**
4. **Ejecutar migraciones**
5. **Configurar SSL/TLS**

### Docker (Opcional)

```bash
# Construir imagen
docker build -t centro-deportivo .

# Ejecutar contenedor
docker run -p 5000:5000 centro-deportivo
```

## 🛠️ Desarrollo

### Comandos Útiles

```bash
# Instalar nueva dependencia
pip install nueva-dependencia
pip freeze > requirements.txt

# Formatear código
black app/ tests/

# Lint del código
flake8 app/ tests/

# Ejecutar aplicación en modo desarrollo
flask run --debug
```

### Estructura de Commits

Seguimos la convención de commits semánticos:

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bugs
- `docs:` Cambios en documentación
- `test:` Añadir o modificar tests
- `refactor:` Refactorización de código

## 👥 Equipo de Desarrollo

- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Backend**: Python, Flask
- **Base de Datos**: SQLAlchemy, PostgreSQL/MySQL/SQLite
- **Testing**: pytest, Selenium, Locust
- **DevOps**: Docker, Nginx, Gunicorn

## 📞 Soporte

### Problemas Comunes

**Error de base de datos**
```bash
flask db upgrade
```

**Problemas de dependencias**
```bash
pip install --upgrade -r requirements.txt
```

**Error de permisos en Windows**
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Contacto

- 📧 Email: [tu-email@ejemplo.com]
- 🐛 Issues: [GitHub Issues]
- 📚 Wiki: [GitHub Wiki]

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 🎯 Próximas Funcionalidades

- [ ] Aplicación móvil React Native
- [ ] Sistema de membresías
- [ ] Integración con redes sociales
- [ ] Dashboard de analytics avanzado
- [ ] API GraphQL
- [ ] Sistema de torneos
- [ ] Chat en tiempo real
- [ ] Notificaciones push

---

**¡Gracias por usar nuestro Sistema de Gestión de Reservas! 🏟️**

# I. Project Directory Structure
## 1. Project directory structure
```
project/
├── app/
│   ├── __init__.py         # Flask app initialization
|   ├── constants           # Contains constant values, such as error messages, HTTP status codes, or configuration values that do not change.
|   ├── context             # Manages application context, request context dat or managing and storing user session data 
|   ├── exceptions          # Defines custom exceptions for the application, such as HTTP exceptions or data processing errors.
│   ├── extensions          # Configures and initializes Flask extensions
|   ├── response            # Handles the standard API response format (e.g., Success, Error).
|   ├── repositories        # Manages database operations, separating query logic and implementing a Data Access Layer (DAL).
│   ├── routes              # Defines API routes (endpoints) and organizes them into modules.
│   ├── models              # Defines database models using Flask-SQLAlchemy.
│   ├── schemas             # Defines data schemas using Marshmallow (or Pydantic if using FastAPI).
│   ├── services            # Contains business logic (Business Logic Layer), performing complex operations.
│   ├── websocket           # Manages WebSocket connections for real-time communication.
│   └── utils/              # Contains utility functions and helper methods.
│   |   ├── __init__.py
│   |   └── helpers.py
│   |   └── ...
│   └── log.py              # Configures logging for the application.
├── requirements.txt        # Python dependencies
├── config.py               # Configuration settings
├── docker                  # Docker
│   └── ...            
├── docker-compose.yml      # Compose file for multi-service setup
└── main.py                 # The main entry point of the Flask application, where the app is launched, and routes are registered.
```

## 2. Directory & best practice
### 2.1 app directory
*Purpose:* Organize your core application, routes, models, services, and schemas by feature or domain within blueprints.

*Example:* For a users feature:
```
app/
├── __init__.py         # Initialize the users blueprint
├── constants           # Constant definitions
├── routes.py           # Route definitions
├── models.py           # Datbase models
├── schemas.py          # Marshmallow schemas
├── services.py         # Business logic

```

### 2.2Centralized Initialization in app/__init__.py

Register app, extensions, and submodules in app/__init__.py

*Example:*
```
from flask import Flask
from app.blueprints.users import users_bp
from app.extensions import db, migrate
from submodules.module1 import models as module1_models

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(users_bp, url_prefix='/users')

    return app
```

### 3.4 Configuration in config.py

Centralize configuration settings (e.g., development, production, testing):

*Example:*
```
class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

```

# II.HOW TO RUN
## 1. Python Packages
### 1.1 Install package
```
pip install -r requirements.txt
```
### 1.2 Install new packages
```
pip install <package_name>
```
### 1.3 Freeze requirements
```
pip freeze > requirements.txt
```
## 2. Run locally
```
fastapi dev main.py
```
## 3. Run by docker
```
docker-compose up
```
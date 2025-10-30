# app/__init__.py

from flask import Flask
from config import Config

# Importar blueprints
from app.routes.auth_routes import auth_bp
from app.routes.exam_routes import exam_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(exam_bp)

    return app

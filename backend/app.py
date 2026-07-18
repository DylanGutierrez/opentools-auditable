"""Point d’entrée Flask du backend Auditable"""
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
""" Import des routes et des services """
from services.system import install_dependencies, setup_database
from services.security_feeds import validate_nvd_api_key
from routes.config_routes import config_bp
from routes.client_routes import client_bp
from routes.convention_routes import convention_bp
from routes.scope_routes import scope_bp
from routes.settings_routes import settings_bp
from routes.logs_routes import logs_bp
from routes.audit_routes import audit_bp
from routes.scan_routes import scan_bp


def create_app():
    """Crée l’application Flask et branche toutes les routes"""
    # Chargement du .env.
    load_dotenv()

    # Vérification des dépendances et de la base au démarrage
    install_dependencies()
    setup_database()

    app = Flask(__name__)
    CORS(app)

    # Vérification de la clé NVD au démarrage
    if os.getenv("NVD_VERIFY_ON_START", "1").strip().lower() in ["1", "true", "yes", "oui", "on"]:
        validate_nvd_api_key(force=True)

    # Enregistrement des différentes familles de routes.
    app.register_blueprint(config_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(convention_bp)
    app.register_blueprint(scope_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(scan_bp)

    return app


# Compatibilité avec le lancement existant : from app import app.
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

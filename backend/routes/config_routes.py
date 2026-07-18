"""Routes config."""
import os
from flask import Blueprint, jsonify
from services.security_feeds import validate_nvd_api_key, get_raw_nvd_api_key

config_bp = Blueprint("config", __name__)

# Récupération du nom de l’auditeur.
@config_bp.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({"username": os.getenv("user_name", "Auditeur")})

# Statut de la clé NVD.
@config_bp.route('/api/nvd/status', methods=['GET'])
def get_nvd_status():
    status = validate_nvd_api_key(force=True)

    return jsonify({
        "configured": bool(get_raw_nvd_api_key()),
        "status": status.get("status"),
        "message": status.get("message")
    })

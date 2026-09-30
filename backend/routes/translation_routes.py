"""Routes de traduction locale avec TranslateGemma."""
from flask import Blueprint, request, jsonify

from services.translation_service import (
    normalize_language,
    translation_status,
    translate_vulnerability_descriptions,
)

translation_bp = Blueprint("translation", __name__)


# Vérification de l'état de TranslateGemma.
@translation_bp.route('/api/translate/status', methods=['GET'])
def get_translate_status():
    return jsonify(translation_status())


# Traduction automatique des descriptions de vulnérabilités.
@translation_bp.route('/api/translate/remediations', methods=['POST'])
def translate_remediations():
    try:
        data = request.get_json(silent=True) or {}
        audit_id = data.get("audit_id")
        language = normalize_language(data.get("language", "fr"))
        force = bool(data.get("force", False))

        if not audit_id:
            return jsonify({"error": "audit_id est obligatoire."}), 400

        result = translate_vulnerability_descriptions(
            audit_id=int(audit_id),
            language=language,
            force=force,
        )

        return jsonify({
            "message": "Traduction terminée.",
            **result,
        })

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        print(f"[!] Erreur /api/translate/remediations : {exc}")
        return jsonify({"error": str(exc)}), 500

"""Routes settings."""
from flask import Blueprint, request, jsonify
from config import NMAP_OUTPUTS, COMMON_OUTPUTS, NUCLEI_SEVERITIES, WPSCAN_ENUM_OPTIONS, NUCLEI_RATE_LIMITS
from database import get_db_connection, get_convention_by_audit
from services.settings_service import (
    get_param_rows,
    normalize_aggressiveness,
    normalize_bool,
    normalize_output,
    normalize_severity,
    normalize_tuning,
    normalize_wpscan_enumeration,
)

settings_bp = Blueprint("settings", __name__)

# Récupération des paramètres.
@settings_bp.route('/api/settings/<int:audit_id>', methods=['GET'])
def get_settings(audit_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        conv = get_convention_by_audit(cursor, audit_id)
        if not conv:
            return jsonify({"error": "Convention introuvable."}), 404

        settings = get_param_rows(cursor)
        conn.commit()

        return jsonify({
            "audit_id": audit_id,
            "signed": bool(conv["signed"]),
            "settings": settings,
            "options": {
                "nmap_output": sorted(NMAP_OUTPUTS),
                "common_output": sorted(COMMON_OUTPUTS),
                "nuclei_severity": NUCLEI_SEVERITIES,
                "wpscan_enumeration": WPSCAN_ENUM_OPTIONS,
                "nuclei_rate_limits": NUCLEI_RATE_LIMITS,
            }
        })

    except Exception as e:
        print(f"[!] Erreur GET /api/settings/{audit_id} : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Vérification des paramètres avant sauvegarde.
@settings_bp.route('/api/settings/<int:audit_id>', methods=['PUT'])
def update_settings(audit_id):
    conn = None
    cursor = None

    try:
        data = request.json or {}
        tool = str(data.get("tool", "")).strip().lower()
        values = data.get("values", {}) or {}

        if tool not in {"nmap", "nikto", "wpscan", "nuclei"}:
            return jsonify({"error": "Outil inconnu."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        conv = get_convention_by_audit(cursor, audit_id)
        if not conv:
            return jsonify({"error": "Convention introuvable."}), 404
        if conv["signed"]:
            return jsonify({"error": "Les paramètres ne peuvent plus être modifiés après signature de la convention."}), 403

        settings = get_param_rows(cursor)
        current = settings[tool]

        if tool == "nmap":
            aggressiveness = normalize_aggressiveness(values.get("aggressiveness", current.get("aggressiveness")))
            output_file = normalize_output(values.get("output_file", current.get("output_file")), NMAP_OUTPUTS)
            cursor.execute(
                "UPDATE param_nmap SET aggressiveness = %s, output_file = %s WHERE id = %s",
                (aggressiveness, output_file, current["id"])
            )

        elif tool == "nikto":
            aggressiveness = normalize_aggressiveness(values.get("aggressiveness", current.get("aggressiveness")))
            output_file = normalize_output(values.get("output_file", current.get("output_file")), COMMON_OUTPUTS)
            tuning_option = normalize_tuning(values.get("tuning_option", current.get("tuning_option")))
            cursor.execute(
                "UPDATE param_nikto SET aggressiveness = %s, output_file = %s, tuning_option = %s WHERE id = %s",
                (aggressiveness, output_file, tuning_option, current["id"])
            )

        elif tool == "wpscan":
            aggressiveness = normalize_bool(values.get("aggressiveness", current.get("aggressiveness")))
            output_file = normalize_output(values.get("output_file", current.get("output_file")), COMMON_OUTPUTS)
            mode, enum_option = normalize_wpscan_enumeration(values.get("enumeration_mode", current.get("enumeration_mode")))
            cursor.execute(
                """
                UPDATE param_wpscan
                SET aggressiveness = %s, output_file = %s, enumeration_mode = %s, enumeration_option = %s
                WHERE id = %s
                """,
                (aggressiveness, output_file, mode, enum_option, current["id"])
            )

        elif tool == "nuclei":
            aggressiveness = normalize_aggressiveness(values.get("aggressiveness", current.get("aggressiveness")))
            output_file = normalize_output(values.get("output_file", current.get("output_file")), COMMON_OUTPUTS)
            severity = normalize_severity(values.get("severity", current.get("severity")))
            cursor.execute(
                "UPDATE param_nuclei SET aggressiveness = %s, output_file = %s, severity = %s WHERE id = %s",
                (aggressiveness, output_file, severity, current["id"])
            )

        conn.commit()
        settings = get_param_rows(cursor)

        return jsonify({
            "message": "Paramètres mis à jour.",
            "signed": bool(conv["signed"]),
            "settings": settings
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"[!] Erreur PUT /api/settings/{audit_id} : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

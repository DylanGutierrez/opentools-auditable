"""Routes convention."""
from flask import Blueprint, jsonify
from database import get_db_connection

convention_bp = Blueprint("convention", __name__)

# Convention signée ou non ?
@convention_bp.route('/api/convention/<int:audit_id>/status', methods=['GET'])
def convention_status(audit_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, signed FROM convention WHERE audit_id = %s", (audit_id,))
        conv = cursor.fetchone()

        if not conv:
            return jsonify({"error": "Aucune convention trouvée pour cet audit."}), 404

        return jsonify({
            "audit_id": audit_id,
            "signed": bool(conv["signed"])
        })

    except Exception as e:
        print(f"[!] Erreur /api/convention/{audit_id}/status : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Signature de la convention après validation du périmètre.
@convention_bp.route('/api/convention/<int:audit_id>/sign', methods=['POST'])
def sign_convention(audit_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, signed FROM convention WHERE audit_id = %s", (audit_id,))
        conv = cursor.fetchone()

        if not conv:
            return jsonify({"error": "Convention introuvable."}), 404

        if conv["signed"]:
            return jsonify({"message": "Convention déjà signée."})

        cursor.execute("SELECT COUNT(*) AS total FROM list_ip WHERE convention_id = %s", (conv["id"],))
        count_ips = cursor.fetchone()["total"]

        if count_ips == 0:
            return jsonify({"error": "Impossible de signer la convention sans au moins une IP dans le périmètre."}), 400

        cursor.execute(
            "UPDATE convention SET signed = TRUE WHERE audit_id = %s",
            (audit_id,)
        )
        conn.commit()

        return jsonify({"message": "Convention signée. Périmètre verrouillé."})

    except Exception as e:
        print(f"[!] Erreur /api/convention/{audit_id}/sign : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

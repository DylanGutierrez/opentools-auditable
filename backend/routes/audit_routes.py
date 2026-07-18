"""Routes audit."""
from flask import Blueprint, request, jsonify
from database import get_db_connection

audit_bp = Blueprint("audit", __name__)

# Récupération des vulnérabilités.
@audit_bp.route('/api/audit/<int:audit_id>/report', methods=['GET'])
def get_audit_report(audit_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                c.id AS client_id,
                c.company_name,
                c.dirigeant,
                a.id AS audit_id,
                a.title,
                a.started_at,
                a.finished_at,
                COALESCE(conv.signed, FALSE) AS convention_signed
            FROM audit a
            LEFT JOIN Client c ON c.id = a.client_id
            LEFT JOIN convention conv ON conv.audit_id = a.id
            WHERE a.id = %s
            LIMIT 1
        """, (audit_id,))
        audit = cursor.fetchone()

        if not audit:
            return jsonify({"error": "Audit introuvable."}), 404

        cursor.execute("""
            SELECT
                v.id,
                v.CVE,
                v.CVSS,
                v.criticity,
                v.description,
                v.remediation,
                v.used_tool,
                v.EPSS,
                v.EPSS_percentile
            FROM vulnerabilities v
            INNER JOIN list_ip li ON li.id = v.ip_id
            INNER JOIN convention conv ON conv.id = li.convention_id
            WHERE conv.audit_id = %s
              AND v.used_tool = 'Nmap'
            ORDER BY v.criticity DESC, v.CVE ASC
        """, (audit_id,))
        vulnerabilities = cursor.fetchall()

        return jsonify({
            "audit": audit,
            "has_results": len(vulnerabilities) > 0,
            "vulnerabilities": vulnerabilities
        })

    except Exception as e:
        print(f"[!] Erreur /api/audit/{audit_id}/report : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Mise à jour des remédiations.
@audit_bp.route('/api/audit/<int:audit_id>/vulnerabilities/<int:vulnerability_id>/remediation', methods=['PUT'])
def update_vulnerability_remediation(audit_id, vulnerability_id):
    conn = None
    cursor = None

    try:
        data = request.get_json(silent=True) or {}

        if "remediation" not in data:
            return jsonify({"error": "Le champ remediation est obligatoire."}), 400

        remediation = data.get("remediation")
        if remediation is None:
            remediation = ""

        if not isinstance(remediation, str):
            return jsonify({"error": "La remédiation doit être une chaîne de caractères."}), 400

        remediation = remediation.strip()
        if len(remediation) > 10000:
            return jsonify({
                "error": "La remédiation ne peut pas dépasser 10 000 caractères."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT v.id
            FROM vulnerabilities v
            INNER JOIN list_ip li ON li.id = v.ip_id
            INNER JOIN convention conv ON conv.id = li.convention_id
            WHERE v.id = %s
              AND conv.audit_id = %s
            LIMIT 1
        """, (vulnerability_id, audit_id))
        vulnerability = cursor.fetchone()

        if not vulnerability:
            return jsonify({
                "error": "Vulnérabilité introuvable pour cet audit."
            }), 404

        stored_remediation = remediation or None
        cursor.execute(
            "UPDATE vulnerabilities SET remediation = %s WHERE id = %s",
            (stored_remediation, vulnerability_id)
        )
        conn.commit()

        return jsonify({
            "message": "Remédiation mise à jour avec succès.",
            "vulnerability_id": vulnerability_id,
            "remediation": stored_remediation
        })

    except Exception as e:
        if conn:
            conn.rollback()
        print(
            f"[!] Erreur PUT /api/audit/{audit_id}/vulnerabilities/"
            f"{vulnerability_id}/remediation : {e}"
        )
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

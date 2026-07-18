"""Routes logs."""
from flask import Blueprint, jsonify
from database import get_db_connection, get_convention_by_audit

logs_bp = Blueprint("logs", __name__)

# Récupération des logs.
@logs_bp.route('/api/logs/<int:audit_id>', methods=['GET'])
def get_logs(audit_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        conv = get_convention_by_audit(cursor, audit_id)
        if not conv:
            return jsonify({"error": "Convention introuvable."}), 404

        cursor.execute("""
            SELECT id, ip, true_cmd_port
            FROM list_ip
            WHERE convention_id = %s
            ORDER BY ip ASC
        """, (conv["id"],))
        targets = cursor.fetchall()

        grouped = {
            target["id"]: {
                "id": target["id"],
                "ip": target["ip"],
                "true_cmd_port": target.get("true_cmd_port"),
                "logs": []
            }
            for target in targets
        }

        log_sources = [
            ("nmap", "log_nmap", "id, list_ip_id, log, NULL AS request, NULL AS enumeration_option, horodatage"),
            ("nikto", "log_nikto", "id, list_ip_id, log, NULL AS request, NULL AS enumeration_option, horodatage"),
            ("wpscan", "log_wpscan", "id, list_ip_id, log, NULL AS request, enumeration_option, horodatage"),
            ("nuclei", "log_nuclei", "id, list_ip_id, log, NULL AS request, NULL AS enumeration_option, horodatage"),
            ("ndv", "log_ndv", "id, list_ip_id, log, request, NULL AS enumeration_option, horodatage"),
            ("circl", "log_circl", "id, list_ip_id, log, request, NULL AS enumeration_option, horodatage"),
        ]

        for tool, table, columns in log_sources:
            cursor.execute(f"""
                SELECT {columns}
                FROM {table}
                WHERE list_ip_id IN (
                    SELECT id FROM list_ip WHERE convention_id = %s
                )
                ORDER BY horodatage DESC
            """, (conv["id"],))
            for row in cursor.fetchall():
                target = grouped.get(row["list_ip_id"])
                if not target:
                    continue
                row["tool"] = tool
                target["logs"].append(row)

        for target in grouped.values():
            target["logs"].sort(key=lambda item: str(item.get("horodatage") or ""), reverse=True)

        return jsonify({
            "audit_id": audit_id,
            "signed": bool(conv["signed"]),
            "targets": list(grouped.values())
        })

    except Exception as e:
        print(f"[!] Erreur GET /api/logs/{audit_id} : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

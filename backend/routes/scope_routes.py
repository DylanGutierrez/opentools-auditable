"""Routes scope."""
import mysql.connector
from flask import Blueprint, request, jsonify
from database import get_db_connection
from services.scan_helpers import build_true_cmd_port, parse_ports_input

scope_bp = Blueprint("scope", __name__)

# Récupération du périmètre IP / Ports.
@scope_bp.route('/api/scope/<int:audit_id>', methods=['GET'])
def get_scope(audit_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, signed FROM convention WHERE audit_id = %s", (audit_id,))
        conv = cursor.fetchone()
        if not conv:
            return jsonify({"error": "Convention introuvable."}), 404

        cursor.execute("""
            SELECT 
                li.id,
                li.ip,
                li.cidr,
                li.environnement,
                li.domaine_name,
                li.true_cmd_port,
                lp.port_number,
                lp.status
            FROM list_ip li
            LEFT JOIN list_port lp ON lp.list_ip_id = li.id
            WHERE li.convention_id = %s
            ORDER BY li.id, lp.port_number
        """, (conv["id"],))
        rows = cursor.fetchall()

        grouped = {}
        for row in rows:
            ip_id = row["id"]
            if ip_id not in grouped:
                grouped[ip_id] = {
                    "id": ip_id,
                    "ip": row["ip"],
                    "cidr": row["cidr"],
                    "environnement": row["environnement"],
                    "domaine_name": row["domaine_name"],
                    "true_cmd_port": row["true_cmd_port"],
                    "ports": []
                }
            if row["port_number"] is not None:
                grouped[ip_id]["ports"].append({
                    "port_number": row["port_number"],
                    "status": row["status"]
                })

        targets = []
        for target in grouped.values():
            target["port_count"] = len(target["ports"])
            targets.append(target)

        return jsonify({
            "audit_id": audit_id,
            "signed": bool(conv["signed"]),
            "targets": targets
        })

    except Exception as e:
        print(f"[!] Erreur /api/scope/{audit_id} : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Limitation de la saisie des IP / Port pour éviter les erreurs.
@scope_bp.route('/api/scope/<int:audit_id>', methods=['POST'])
def add_scope_target(audit_id):
    conn = None
    cursor = None

    try:
        data = request.json or {}
        ip = data.get("ip", "").strip()
        ports_raw = data.get("ports", "").strip()

        if not ip:
            return jsonify({"error": "IP manquante."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, signed FROM convention WHERE audit_id = %s", (audit_id,))
        conv = cursor.fetchone()
        if not conv:
            return jsonify({"error": "Convention introuvable."}), 404
        if conv["signed"]:
            return jsonify({"error": "Le périmètre est verrouillé après signature de la convention."}), 403

        true_cmd_port = build_true_cmd_port(ports_raw)

        cursor.execute("""
            INSERT INTO list_ip (ip, convention_id, cidr, environnement, domaine_name, deepscan, true_cmd_port)
            VALUES (%s, %s, %s, %s, %s, FALSE, %s)
        """, (ip, conv["id"], None, None, None, true_cmd_port))
        list_ip_id = cursor.lastrowid

        ports = parse_ports_input(ports_raw)

        for port in ports:
            cursor.execute("""
                INSERT INTO list_port (port_number, list_ip_id, status)
                VALUES (%s, %s, %s)
            """, (port, list_ip_id, "pending"))

        conn.commit()
        return jsonify({"message": "IP ajoutée au périmètre."})

    except mysql.connector.errors.IntegrityError:
        return jsonify({"error": "Cette IP existe déjà dans le périmètre."}), 409
    except Exception as e:
        print(f"[!] Erreur POST /api/scope/{audit_id} : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Modification du périmètre tant que la convention n’est pas signée.
@scope_bp.route('/api/scope/<int:audit_id>/<int:list_ip_id>', methods=['PUT'])
def update_scope_target(audit_id, list_ip_id):
    conn = None
    cursor = None

    try:
        data = request.json or {}
        ip = data.get("ip", "").strip()
        ports_raw = data.get("ports", "").strip()

        if not ip:
            return jsonify({"error": "IP manquante."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, signed FROM convention WHERE audit_id = %s", (audit_id,))
        conv = cursor.fetchone()
        if not conv:
            return jsonify({"error": "Convention introuvable."}), 404
        if conv["signed"]:
            return jsonify({"error": "Le périmètre est verrouillé après signature de la convention."}), 403

        cursor.execute("""
            SELECT id FROM list_ip
            WHERE id = %s AND convention_id = %s
        """, (list_ip_id, conv["id"]))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"error": "Cible introuvable."}), 404

        true_cmd_port = build_true_cmd_port(ports_raw)

        cursor.execute("""
            UPDATE list_ip
            SET ip = %s,
                true_cmd_port = %s
            WHERE id = %s
        """, (ip, true_cmd_port, list_ip_id))

        cursor.execute("DELETE FROM list_port WHERE list_ip_id = %s", (list_ip_id,))

        ports = parse_ports_input(ports_raw)

        for port in ports:
            cursor.execute("""
                INSERT INTO list_port (port_number, list_ip_id, status)
                VALUES (%s, %s, %s)
            """, (port, list_ip_id, "pending"))

        conn.commit()
        return jsonify({"message": "IP / port(s) modifiée."})

    except mysql.connector.errors.IntegrityError:
        return jsonify({"error": "Cette IP existe déjà dans le périmètre."}), 409
    except Exception as e:
        print(f"[!] Erreur PUT /api/scope/{audit_id}/{list_ip_id} : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Suppression d’une cible du périmètre.
@scope_bp.route('/api/scope/<int:audit_id>/<int:list_ip_id>', methods=['DELETE'])
def delete_scope_target(audit_id, list_ip_id):
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
            return jsonify({"error": "Le périmètre est verrouillé après signature de la convention."}), 403

        cursor.execute("""
            SELECT id FROM list_ip
            WHERE id = %s AND convention_id = %s
        """, (list_ip_id, conv["id"]))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"error": "Cible introuvable."}), 404

        cursor.execute("DELETE FROM list_port WHERE list_ip_id = %s", (list_ip_id,))
        cursor.execute("DELETE FROM list_ip WHERE id = %s", (list_ip_id,))
        conn.commit()

        return jsonify({"message": "Cible supprimée."})

    except Exception as e:
        print(f"[!] Erreur DELETE /api/scope/{audit_id}/{list_ip_id} : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

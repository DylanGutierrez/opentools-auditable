"""Routes client."""
from flask import Blueprint, request, jsonify
from database import get_db_connection, ensure_audit_and_convention

client_bp = Blueprint("client", __name__)

# Gestion du client : lecture, création et modification.
@client_bp.route('/api/client', methods=['GET', 'POST', 'PUT'])
def handle_client():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute("SELECT * FROM Client LIMIT 1")
            client = cursor.fetchone()

            if not client:
                return jsonify(None)

            audit_id = ensure_audit_and_convention(cursor, client["id"], client["company_name"])
            conn.commit()

            cursor.execute("""
                SELECT 
                    c.*,
                    a.id AS audit_id,
                    COALESCE(conv.signed, FALSE) AS convention_signed
                FROM Client c
                LEFT JOIN audit a ON a.client_id = c.id
                LEFT JOIN convention conv ON conv.audit_id = a.id
                WHERE c.id = %s
                LIMIT 1
            """, (client["id"],))
            client_full = cursor.fetchone()
            return jsonify(client_full)

        data = request.json or {}

        required_fields = [
            "company_name",
            "dirigeant",
            "adresse",
            "postal_code",
            "contact_mail",
            "contact_phone"
        ]

        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            return jsonify({"error": f"Champs manquants : {', '.join(missing)}"}), 400

        if request.method == 'POST':
            cursor.execute("SELECT COUNT(*) as count FROM Client")
            if cursor.fetchone()['count'] > 0:
                return jsonify({"error": "Un client existe déjà."}), 403

            cursor.execute("""
                INSERT INTO Client (
                    company_name, dirigeant, adresse, postal_code, contact_mail, contact_phone
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data['company_name'],
                data['dirigeant'],
                data['adresse'],
                data['postal_code'],
                data['contact_mail'],
                data['contact_phone']
            ))
            client_id = cursor.lastrowid

            audit_id = ensure_audit_and_convention(cursor, client_id, data["company_name"])
            conn.commit()

            return jsonify({
                "message": "Client ajouté",
                "id": client_id,
                "audit_id": audit_id
            })

        if request.method == 'PUT':
            cursor.execute("""
                SELECT 
                    c.id,
                    COALESCE(conv.signed, FALSE) AS convention_signed
                FROM Client c
                LEFT JOIN audit a ON a.client_id = c.id
                LEFT JOIN convention conv ON conv.audit_id = a.id
                LIMIT 1
            """)
            existing = cursor.fetchone()

            if not existing:
                return jsonify({"error": "Aucun client à modifier."}), 404

            if existing["convention_signed"]:
                return jsonify({"error": "Le client ne peut plus être modifié après signature de la convention."}), 403

            cursor.execute("""
                UPDATE Client
                SET company_name = %s,
                    dirigeant = %s,
                    adresse = %s,
                    postal_code = %s,
                    contact_mail = %s,
                    contact_phone = %s
                WHERE id = %s
            """, (
                data['company_name'],
                data['dirigeant'],
                data['adresse'],
                data['postal_code'],
                data['contact_mail'],
                data['contact_phone'],
                existing['id']
            ))
            conn.commit()

            return jsonify({"message": "Client modifié avec succès."})

    except Exception as e:
        print(f"[!] Erreur /api/client : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

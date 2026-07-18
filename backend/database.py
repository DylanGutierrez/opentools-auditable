"""Accès MySQL et helpers communs pour Client/Audit/Convention."""
import os
import mysql.connector


# Connexion à la base depuis le .env.
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "auditable"),
        password=os.getenv("DB_PASS", "admin1auditable"),
        database=os.getenv("DB_NAME", "opentools_auditable")
    )

# Création automatique de l’audit et de la convention du client.
def ensure_audit_and_convention(cursor, client_id, company_name):
    cursor.execute("SELECT id FROM audit WHERE client_id = %s LIMIT 1", (client_id,))
    audit = cursor.fetchone()

    if audit:
        audit_id = audit["id"] if isinstance(audit, dict) else audit[0]
    else:
        cursor.execute(
            "INSERT INTO audit (started_at, client_id, title) VALUES (NOW(), %s, %s)",
            (client_id, f"Audit initial - {company_name}")
        )
        audit_id = cursor.lastrowid

    cursor.execute("SELECT id FROM convention WHERE audit_id = %s LIMIT 1", (audit_id,))
    conv = cursor.fetchone()

    if not conv:
        cursor.execute(
            "INSERT INTO convention (audit_id, signed) VALUES (%s, FALSE)",
            (audit_id,)
        )

    return audit_id

# Convention signée ou non ?
def get_convention_by_audit(cursor, audit_id):
    cursor.execute("SELECT id, signed FROM convention WHERE audit_id = %s", (audit_id,))
    return cursor.fetchone()

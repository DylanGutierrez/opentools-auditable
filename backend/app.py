import os
import re
import time
import shutil
import subprocess
import requests
import mysql.connector

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from mysql.connector import Error


load_dotenv()


def run_cmd(cmd, cwd=None, quiet=False, check=False):
    kwargs = {"cwd": cwd}
    if quiet:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    return subprocess.run(cmd, check=check, **kwargs)


def start_service(service_name):
    result = subprocess.run(
        ["systemctl", "start", service_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def install_dependencies():
    print("[*] Vérification des dépendances système...")

    tools = {
        "nmap": "nmap",
        "wpscan": "wpscan",
        "nikto": "nikto",
        "nuclei": "nuclei",
    }

    for cmd, package in tools.items():
        if shutil.which(cmd) is None:
            print(f"[-] {cmd} manquant. Installation de {package}...")
            run_cmd(["apt-get", "update"], quiet=True)
            run_cmd(["apt-get", "install", "-y", package], quiet=True)

    if shutil.which("mysql") is None:
        print("[*] Client mysql manquant. Installation de MariaDB...")
        run_cmd(["apt-get", "update"], quiet=True)
        run_cmd(["apt-get", "install", "-y", "mariadb-server", "mariadb-client"], quiet=True)

    if shutil.which("nmap") is not None:
        run_cmd(["nmap", "--script-updatedb"], quiet=True)


def start_database_service():
    print("[*] Démarrage du service de base de données...")

    for service_name in ["mariadb", "mysql"]:
        if start_service(service_name):
            print(f"[*] Service démarré : {service_name}")
            return service_name

    raise RuntimeError("Impossible de démarrer le service MariaDB/MySQL.")


def wait_for_mysql(host="127.0.0.1", user="auditable", password="admin1auditable", timeout=20):
    print("[*] Attente du démarrage de MySQL/MariaDB...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password
            )
            conn.close()
            print("[*] Base de données prête.")
            return True
        except Error:
            time.sleep(1)

    return False


def init_db():
    print("[*] Initialisation de la base depuis schema.sql...")

    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "auditable"),
            password=os.getenv("DB_PASS", "admin1auditable")
        )
        cursor = conn.cursor()

        with open("schema.sql", "r", encoding="utf-8") as f:
            sql_script = f.read()

        statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]

        for statement in statements:
            cursor.execute(statement)

        conn.commit()
        print("[*] Base de données initialisée avec succès.")

    except Error as e:
        print(f"[!] Erreur DB init: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def setup_database():
    start_database_service()
    time.sleep(2)

    if not wait_for_mysql(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "auditable"),
        password=os.getenv("DB_PASS", "admin1auditable")
    ):
        raise RuntimeError("MySQL/MariaDB ne répond pas avec les identifiants configurés.")

    init_db()


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "auditable"),
        password=os.getenv("DB_PASS", "admin1auditable"),
        database=os.getenv("DB_NAME", "opentools_auditable")
    )


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


def fetch_cve_details(cve_id):
    nvd_url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"

    nvd_data = {}

    try:
        r = requests.get(nvd_url, timeout=10)
        if r.status_code == 200:
            vulns = r.json().get("vulnerabilities", [])
            if vulns:
                v = vulns[0]["cve"]

                description = ""
                if v.get("descriptions"):
                    description = v["descriptions"][0].get("value", "")

                cvss = ""
                criticity = 0.0
                metrics = v.get("metrics", {})
                if metrics.get("cvssMetricV31"):
                    cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
                    cvss = cvss_data.get("vectorString", "")
                    criticity = cvss_data.get("baseScore", 0.0)

                cwe = ""
                if v.get("weaknesses"):
                    weakness_desc = v["weaknesses"][0].get("description", [])
                    if weakness_desc:
                        cwe = weakness_desc[0].get("value", "")

                remediation = ""

                nvd_data = {
                    "description": description,
                    "cvss": cvss,
                    "criticity": criticity,
                    "cwe": cwe,
                    "remediation": remediation
                }
    except Exception as e:
        print(f"[!] Erreur NVD pour {cve_id}: {e}")

    return nvd_data


def update_epss_for_cve(cursor, cve_id):
    epss_url = f"https://vulnerability.circl.lu/api/epss/{cve_id}"

    try:
        r = requests.get(epss_url, timeout=10)
        if r.status_code != 200:
            print(f"[!] EPSS HTTP {r.status_code} pour {cve_id}")
            return False

        payload = r.json()
        data = payload.get("data", [])

        if not data:
            print(f"[!] Aucune donnée EPSS pour {cve_id}")
            return False

        epss_value = data[0].get("epss")
        percentile_value = data[0].get("percentile")

        epss_float = float(epss_value) * 100 if epss_value is not None else None
        percentile_float = float(percentile_value) * 100 if percentile_value is not None else None

        cursor.execute("""
            UPDATE vulnerabilities
            SET EPSS = %s,
                EPSS_percentile = %s
            WHERE CVE = %s
        """, (epss_float, percentile_float, cve_id))

        return True

    except Exception as e:
        print(f"[!] Erreur EPSS pour {cve_id}: {e}")
        return False
        

def build_true_cmd_port(ports_raw):
    if not ports_raw:
        return ""

    ports_raw = ports_raw.strip()
    if not ports_raw:
        return ""

    return ports_raw


install_dependencies()
setup_database()

app = Flask(__name__)
CORS(app)


@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({"username": os.getenv("user_name", "Auditeur")})


@app.route('/api/client', methods=['GET', 'POST', 'PUT'])
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


@app.route('/api/convention/<int:audit_id>/status', methods=['GET'])
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


@app.route('/api/convention/<int:audit_id>/sign', methods=['POST'])
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


@app.route('/api/scope/<int:audit_id>', methods=['GET'])
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


@app.route('/api/scope/<int:audit_id>', methods=['POST'])
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

        ports = []
        if ports_raw:
            for p in ports_raw.split(","):
                p = p.strip()
                if not p:
                    continue
                if "-" in p:
                    start, end = p.split("-", 1)
                    for port in range(int(start), int(end) + 1):
                        ports.append(port)
                else:
                    ports.append(int(p))

        for port in sorted(set(ports)):
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


@app.route('/api/scope/<int:audit_id>/<int:list_ip_id>', methods=['PUT'])
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

        ports = []
        if ports_raw:
            for p in ports_raw.split(","):
                p = p.strip()
                if not p:
                    continue
                if "-" in p:
                    start, end = p.split("-", 1)
                    for port in range(int(start), int(end) + 1):
                        ports.append(port)
                else:
                    ports.append(int(p))

        for port in sorted(set(ports)):
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


@app.route('/api/scope/<int:audit_id>/<int:list_ip_id>', methods=['DELETE'])
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


@app.route('/api/audit/<int:audit_id>/report', methods=['GET'])
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
                id,
                CVE,
                CVSS,
                criticity,
                description,
                remediation,
                used_tool,
                EPSS,
                EPSS_percentile
            FROM vulnerabilities
            WHERE used_tool = 'Nmap'
            ORDER BY criticity DESC, CVE ASC
        """)
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


@app.route('/api/scan/launch', methods=['POST'])
def launch_scan():
    conn = None
    cursor = None

    try:
        data = request.json or {}
        audit_id = data.get("audit_id")

        if not audit_id:
            return jsonify({"error": "audit_id manquant."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, signed FROM convention WHERE audit_id = %s", (audit_id,))
        conv = cursor.fetchone()

        if not conv or not conv['signed']:
            return jsonify({"error": "La convention d'audit doit être signée pour lancer une analyse."}), 403

        cursor.execute("""
            SELECT li.ip, lp.port_number
            FROM list_ip li
            LEFT JOIN list_port lp ON lp.list_ip_id = li.id
            WHERE li.convention_id = %s
        """, (conv["id"],))
        rows = cursor.fetchall()

        grouped = {}
        for row in rows:
            ip = row["ip"]
            if ip not in grouped:
                grouped[ip] = []
            if row["port_number"] is not None:
                grouped[ip].append(row["port_number"])

        results = {}

        for ip, ports in grouped.items():
            cmd = ["nmap", "-sV", "--script", "vulners", ip]
            if ports:
                cmd.extend(["-p", ",".join(str(p) for p in sorted(set(ports)))])

            proc = subprocess.run(cmd, capture_output=True, text=True)

            print(f"[*] Commande lancée : {' '.join(cmd)}")
            print(f"[*] Return code : {proc.returncode}")
            print(f"[*] STDOUT :\n{proc.stdout}")
            print(f"[*] STDERR :\n{proc.stderr}")

            results[ip] = {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "returncode": proc.returncode
            }

            cves = re.findall(r"(CVE-\d{4}-\d{4,7})", proc.stdout)
            print(f"[*] CVE trouvées pour {ip} : {cves}")

            for cve in set(cves):
                details = fetch_cve_details(cve)

                cursor.execute("SELECT id FROM vulnerabilities WHERE CVE = %s LIMIT 1", (cve,))
                existing_vuln = cursor.fetchone()

                if not existing_vuln:
                    cursor.execute("""
                        INSERT INTO vulnerabilities (
                            CVE, CVSS, description, criticity, CWE, remediation, used_tool
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        cve,
                        details.get('cvss'),
                        details.get('description'),
                        details.get('criticity'),
                        details.get('cwe'),
                        details.get('remediation'),
                        'Nmap'
                    ))

                updated = update_epss_for_cve(cursor, cve)
                print(f"[*] EPSS mis à jour pour {cve} : {updated}")

            conn.commit()

        return jsonify({"message": "Analyse lancée avec succès.", "raw": results})

    except Exception as e:
        print(f"[!] Erreur /api/scan/launch : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

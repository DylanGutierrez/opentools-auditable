"""Installation, démarrage système et migrations runtime."""
import os
import time
import shutil
import subprocess
import mysql.connector
from mysql.connector import Error


# Fonction utilitaire système.
def run_cmd(cmd, cwd=None, quiet=False, check=False):
    kwargs = {"cwd": cwd}
    if quiet:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    return subprocess.run(cmd, check=check, **kwargs)

# Fonction utilitaire système.
def start_service(service_name):
    result = subprocess.run(
        ["systemctl", "start", service_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

# Vérification et installation des outils système utiles au scan.
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

# Démarrage de MariaDB/MySQL.
def start_database_service():
    print("[*] Démarrage du service de base de données...")

    for service_name in ["mariadb", "mysql"]:
        if start_service(service_name):
            print(f"[*] Service démarré : {service_name}")
            return service_name

    raise RuntimeError("Impossible de démarrer le service MariaDB/MySQL.")

# Attente de la disponibilité de la base de données.
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

# Import du schema.sql.
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

# Petites migrations qui évitent de casser une base existante.
def ensure_runtime_schema():
    """Applique les petites migrations nécessaires au runtime sans casser une base existante."""
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "auditable"),
            password=os.getenv("DB_PASS", "admin1auditable"),
            database=os.getenv("DB_NAME", "opentools_auditable")
        )
        cursor = conn.cursor()

        for table in ["log_ndv", "log_circl", "log_nmap", "log_nikto", "log_wpscan", "log_nuclei"]:
            try:
                cursor.execute(f"ALTER TABLE {table} MODIFY log LONGTEXT")
            except Error as e:
                print(f"[!] Migration ignorée pour {table}.log : {e}")

        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'list_ip'
                  AND COLUMN_NAME = 'true_cmd_port'
            """)
            exists = cursor.fetchone()[0]
            if not exists:
                cursor.execute("ALTER TABLE list_ip ADD COLUMN true_cmd_port TEXT")
        except Error as e:
            print(f"[!] Migration ignorée pour list_ip.true_cmd_port : {e}")

        conn.commit()
        print("[*] Vérification/migration runtime de la base terminée.")

    except Error as e:
        print(f"[!] Erreur migration runtime DB : {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Préparation complète de la base avant le lancement Flask.
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
    ensure_runtime_schema()

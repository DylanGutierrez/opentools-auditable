"""Création des fichiers de rapport et sauvegarde des logs."""
import os
import re
import random
from datetime import datetime
from config import REPORT_ROOT


# Création du dossier de rapport si besoin.
def ensure_report_dir(tool):
    directory = os.path.join(REPORT_ROOT, tool)
    os.makedirs(directory, exist_ok=True)
    return directory

# Nom unique pour éviter d’écraser un rapport.
def unique_report_name(tool, ip=None, suffix=""):
    safe_ip = re.sub(r"[^A-Za-z0-9_.-]", "_", ip or "target")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    rand = random.randint(1000, 9999)
    suffix = f"_{suffix}" if suffix else ""
    return f"{tool}_{safe_ip}_{timestamp}_{rand}{suffix}"

# Construction du chemin final du rapport.
def report_path(tool, name, ext=None):
    directory = ensure_report_dir(tool)
    filename = f"{name}.{ext}" if ext else name
    return os.path.join(directory, filename)

# Écriture du rapport sur le disque.
def write_text_report(tool, content, ext="txt", ip=None, suffix=""):
    name = unique_report_name(tool, ip=ip, suffix=suffix)
    path = report_path(tool, name, ext)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content or "")
    return path

# Sauvegarde des réponses outils/API sans bloquer le scan.
def log_site_response(cursor, table, list_ip_id, request_text, response_text, report_tool):
    report_ext = "json" if response_text and response_text.strip().startswith(("{", "[")) else "txt"
    report_file = write_text_report(report_tool, response_text, report_ext, ip=str(list_ip_id), suffix="api")

    # Le rapport complet est conservé dans /rapports.
    # En base, on stocke le chemin + un extrait afin qu'un log trop long ne bloque jamais le scan.
    try:
        max_db_log_size = int(os.getenv("DB_LOG_MAX_CHARS", "60000"))
    except ValueError:
        max_db_log_size = 60000

    if response_text and len(response_text) > max_db_log_size:
        db_response_text = (
            response_text[:max_db_log_size]
            + "\n\n[TRONQUÉ] Réponse complète disponible dans le fichier : "
            + report_file
        )
    else:
        db_response_text = response_text or ""

    log_text = f"Rapport sauvegardé : {report_file}\n\n{db_response_text}"

    try:
        cursor.execute(
            f"INSERT INTO {table} (list_ip_id, request, log) VALUES (%s, %s, %s)",
            (list_ip_id, request_text, log_text)
        )
    except Exception as e:
        print(f"[!] Impossible d'insérer le log dans {table}: {e}")
        print(f"[*] Rapport complet quand même sauvegardé : {report_file}")

    return report_file

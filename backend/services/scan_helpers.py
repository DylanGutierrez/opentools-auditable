"""Helpers utilisés pendant les scans."""
import re
import subprocess
from config import NMAP_OUTPUTS, COMMON_OUTPUTS
from services.reports import unique_report_name, report_path
from services.settings_service import normalize_output


# Conservation de la saisie IP / Port originale.
def build_true_cmd_port(ports_raw):
    if not ports_raw:
        return ""

    ports_raw = ports_raw.strip()
    if not ports_raw:
        return ""

    if ports_raw.lower() == "auto":
        return "auto"

    return ports_raw

# Exécution d’une commande de scan.
def run_scan_command(cmd):
    print(f"[*] Commande lancée : {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(f"[*] Return code : {proc.returncode}")
    if proc.stdout:
        print(f"[*] STDOUT :\n{proc.stdout}")
    if proc.stderr:
        print(f"[*] STDERR :\n{proc.stderr}")
    return proc

# Préparation du texte de log de commande.
def command_log_text(cmd, proc, report_files=None, context=None):
    report_files = report_files or []
    parts = [
        f"Commande : {' '.join(cmd)}",
        f"Code retour : {proc.returncode}",
    ]
    if context:
        parts.append(f"Contexte : {context}")
    if report_files:
        parts.append("Rapport(s) : " + ", ".join(report_files))
    parts.extend([
        "",
        "STDOUT:",
        proc.stdout or "",
        "",
        "STDERR:",
        proc.stderr or "",
    ])
    return "\n".join(parts)

# Insertion du log outil en base.
def insert_tool_log(cursor, table, list_ip_id, log_text, enumeration_option=None):
    if table == "log_wpscan":
        cursor.execute(
            "INSERT INTO log_wpscan (list_ip_id, log, enumeration_option) VALUES (%s, %s, %s)",
            (list_ip_id, log_text, enumeration_option)
        )
    else:
        cursor.execute(
            f"INSERT INTO {table} (list_ip_id, log) VALUES (%s, %s)",
            (list_ip_id, log_text)
        )

# Limitation de la saisie des IP / Port pour éviter les erreurs.
def parse_ports_input(ports_raw):
    ports_raw = (ports_raw or "").strip()
    if not ports_raw or ports_raw.lower() == "auto":
        return []
    ports = []
    for p in ports_raw.split(","):
        p = p.strip()
        if not p:
            continue
        if "-" in p:
            start, end = p.split("-", 1)
            start = int(start)
            end = int(end)
            if start < 1 or end > 65535 or start > end:
                raise ValueError("Plage de ports invalide.")
            ports.extend(range(start, end + 1))
        else:
            port = int(p)
            if port < 1 or port > 65535:
                raise ValueError("Port invalide.")
            ports.append(port)
    return sorted(set(ports))

# Lecture des ports ouverts trouvés par Nmap.
def parse_nmap_open_ports(output):
    ports = set()
    for match in re.finditer(r"(?m)^(\d{1,5})/(tcp|udp)\s+open\b", output or ""):
        port = int(match.group(1))
        if 1 <= port <= 65535:
            ports.add(port)
    return sorted(ports)

# Ajout de l’export Nmap demandé.
def add_nmap_export(cmd, setting, ip, suffix=""):
    output_file = normalize_output(setting.get("output_file"), NMAP_OUTPUTS)
    if not output_file:
        return []
    base = unique_report_name("nmap", ip=ip, suffix=suffix)
    if output_file == "xml":
        path = report_path("nmap", base, "xml")
        cmd.extend(["-oX", path])
        return [path]
    if output_file == "txt":
        path = report_path("nmap", base, "txt")
        cmd.extend(["-oN", path])
        return [path]
    prefix = report_path("nmap", base, None)
    cmd.extend(["-oA", prefix])
    return [prefix + ".nmap", prefix + ".gnmap", prefix + ".xml"]

# Ajout de l’export Nikto demandé.
def add_nikto_export(cmd, setting, ip):
    output_file = normalize_output(setting.get("output_file"), COMMON_OUTPUTS)
    if not output_file:
        return []
    formats = ["htm", "sql", "txt", "json", "xml"] if output_file == "all" else [output_file]
    base = unique_report_name("nikto", ip=ip)
    if len(formats) == 1:
        ext = formats[0]
        path = report_path("nikto", base, ext)
    else:
        path = report_path("nikto", base, None)
    cmd.extend(["-o", path, "-Format", ",".join(formats)])
    return [path if len(formats) > 1 else path]

# Ajout de l’export WPScan demandé.
def add_wpscan_export(cmd, setting, ip):
    output_file = normalize_output(setting.get("output_file"), COMMON_OUTPUTS)
    if not output_file:
        return []
    output_file = "json" if output_file == "all" else output_file
    base = unique_report_name("wpscan", ip=ip)
    path = report_path("wpscan", base, output_file)
    if output_file == "json":
        cmd.extend(["--format", "json", "--output", path])
    else:
        cmd.extend(["--output", path])
    return [path]

# Ajout de l’export Nuclei demandé.
def add_nuclei_export(cmd, setting, ip, suffix=""):
    output_file = normalize_output(setting.get("output_file"), COMMON_OUTPUTS)
    if not output_file:
        return []
    base = unique_report_name("nuclei", ip=ip, suffix=suffix)
    reports = []
    if output_file == "json":
        path = report_path("nuclei", base, "json")
        cmd.extend(["-json-export", path])
        reports.append(path)
    elif output_file in {"txt", "csv", "xml", "sql"}:
        path = report_path("nuclei", base, output_file)
        cmd.extend(["-o", path])
        reports.append(path)
    elif output_file in {"htm", "html"}:
        path = report_path("nuclei", base, "md")
        cmd.extend(["-markdown-export", path])
        reports.append(path)
    elif output_file == "all":
        json_path = report_path("nuclei", base, "json")
        txt_path = report_path("nuclei", base, "txt")
        md_path = report_path("nuclei", base, "md")
        cmd.extend(["-json-export", json_path, "-markdown-export", md_path, "-o", txt_path])
        reports.extend([json_path, txt_path, md_path])
    return reports

# Création des URLs http/https à scanner.
def tool_target_urls(ip, ports):
    web_ports = [p for p in ports if p in {80, 443, 8080, 8443, 8000, 8888}]
    if not web_ports:
        return [f"https://{ip}"]
    urls = []
    for port in web_ports:
        scheme = "https" if port in {443, 8443} else "http"
        if port in {80, 443}:
            urls.append(f"{scheme}://{ip}")
        else:
            urls.append(f"{scheme}://{ip}:{port}")
    return urls

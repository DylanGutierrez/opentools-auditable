"""Configuration globale du backend Auditable."""
import os
from dotenv import load_dotenv

# Chargement du fichier .env.
load_dotenv()

# Dossier de sortie des rapports générés par les outils.
REPORT_ROOT = os.getenv("REPORT_ROOT", "/rapports")

# Formats autorisés pour les exports.
NMAP_OUTPUTS = {"xml", "txt", "all"}
COMMON_OUTPUTS = {"htm", "html", "csv", "txt", "json", "xml", "sql", "all"}

# Options disponibles pour Nuclei, WPScan et Nikto.
NUCLEI_SEVERITIES = ["info", "low", "medium", "high", "critical"]
NUCLEI_RATE_LIMITS = {
    0: 10,
    1: 20,
    2: 40,
    3: 80,
    4: 100,
    5: 150,
    6: 200,
    7: 250,
    8: 300,
    9: 500,
}
WPSCAN_ENUM_OPTIONS = {
    "vulnerable": "-e vp,vt,tt,cb,dbe,u,m",
    "complete": "-e ap,at,tt,cb,dbe,u,m",
}
NIKTO_TUNING_ALLOWED = set("1234567890abcd")

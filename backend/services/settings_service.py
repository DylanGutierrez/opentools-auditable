"""Validation et lecture des paramètres des outils."""
from config import (
    NMAP_OUTPUTS,
    COMMON_OUTPUTS,
    NUCLEI_SEVERITIES,
    WPSCAN_ENUM_OPTIONS,
    NIKTO_TUNING_ALLOWED,
)


# Vérification du format de sortie demandé.
def normalize_output(value, allowed):
    if value in (None, "", "none"):
        return None
    value = str(value).strip().lower()
    if value == "html":
        value = "htm"
    if value not in allowed:
        raise ValueError(f"Format de sortie non autorisé : {value}")
    return value

# Vérification des paramètres d’agressivité.
def normalize_aggressiveness(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError("L'agressivité doit être un entier entre 0 et 9.")
    if value < 0 or value > 9:
        raise ValueError("L'agressivité doit être comprise entre 0 et 9.")
    return value

# Conversion simple en booléen.
def normalize_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "oui", "on"}
    return False

# Vérification du tuning Nikto.
def normalize_tuning(value):
    if not value:
        return None
    value = "".join(str(value).split()).lower()
    invalid = [char for char in value if char not in NIKTO_TUNING_ALLOWED]
    if invalid:
        raise ValueError("Le tuning Nikto ne peut contenir que : 0-9 et a-d.")
    return "".join(dict.fromkeys(value))

# Vérification des criticités Nuclei.
def normalize_severity(value):
    if isinstance(value, list):
        values = [str(item).strip().lower() for item in value]
    else:
        values = [item.strip().lower() for item in str(value or "").split(",")]
    values = [item for item in values if item]
    invalid = [item for item in values if item not in NUCLEI_SEVERITIES]
    if invalid:
        raise ValueError(f"Criticité Nuclei non autorisée : {', '.join(invalid)}")
    if not values:
        raise ValueError("Au moins une criticité Nuclei doit être sélectionnée.")
    return ",".join(dict.fromkeys(values))

# Vérification de l’énumération WPScan.
def normalize_wpscan_enumeration(mode):
    mode = str(mode or "vulnerable").strip().lower()
    if mode not in WPSCAN_ENUM_OPTIONS:
        raise ValueError("L'énumération WPScan doit être 'vulnerable' ou 'complete'.")
    return mode, WPSCAN_ENUM_OPTIONS[mode]

# Création des lignes de paramètres par défaut.
def ensure_param_rows(cursor):
    cursor.execute("INSERT INTO param_nmap (aggressiveness, output_file) SELECT 0, NULL WHERE NOT EXISTS (SELECT 1 FROM param_nmap)")
    cursor.execute("INSERT INTO param_nikto (aggressiveness, tuning_option, output_file) SELECT 0, NULL, NULL WHERE NOT EXISTS (SELECT 1 FROM param_nikto)")
    cursor.execute("""
        INSERT INTO param_wpscan (aggressiveness, output_file, enumeration_mode, enumeration_option)
        SELECT FALSE, NULL, 'vulnerable', '-e vp,vt,tt,cb,dbe,u,m'
        WHERE NOT EXISTS (SELECT 1 FROM param_wpscan)
    """)
    cursor.execute("""
        INSERT INTO param_nuclei (aggressiveness, severity, output_file)
        SELECT 0, 'info,low,medium,high,critical', NULL
        WHERE NOT EXISTS (SELECT 1 FROM param_nuclei)
    """)

# Récupération des paramètres des outils.
def get_param_rows(cursor):
    ensure_param_rows(cursor)
    cursor.execute("SELECT * FROM param_nmap ORDER BY id LIMIT 1")
    nmap = cursor.fetchone()
    cursor.execute("SELECT * FROM param_nikto ORDER BY id LIMIT 1")
    nikto = cursor.fetchone()
    cursor.execute("SELECT * FROM param_wpscan ORDER BY id LIMIT 1")
    wpscan = cursor.fetchone()
    cursor.execute("SELECT * FROM param_nuclei ORDER BY id LIMIT 1")
    nuclei = cursor.fetchone()
    return {
        "nmap": nmap,
        "nikto": nikto,
        "wpscan": wpscan,
        "nuclei": nuclei,
    }

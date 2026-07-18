"""Récupération NVD et EPSS pour enrichir les vulnérabilités."""
import os
import time
import json
import requests
from services.reports import log_site_response

# État de la clé NVD pendant l’exécution.
NVD_API_KEY_STATUS = {
    "checked": False,
    "key": None,
    "status": "not_checked",
    "message": "Clé NVD non vérifiée.",
}
NVD_LAST_REQUEST_AT = 0


# Conversion sûre des réponses API en texte.
def safe_response_text(response):
    try:
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
    except Exception:
        return response.text or ""

# Calcul simple du niveau de risque depuis le score.
def risk_from_score(score):
    if score is None:
        return ""

    try:
        score = float(score)
    except (TypeError, ValueError):
        return ""

    if score >= 9.0:
        return "Critical"
    if score >= 7.0:
        return "High"
    if score >= 4.0:
        return "Medium"
    if score > 0:
        return "Low"
    return "None"

# Récupération du premier lien externe NVD.
def extract_first_reference_url(cve_data):
    references = cve_data.get("references", [])

    # Format historique possible : {"referenceData": [...]}
    if isinstance(references, dict):
        references = references.get("referenceData", [])

    # Format NVD 2.0 actuel : [{"url": "...", "source": "..."}, ...]
    if isinstance(references, list):
        for reference in references:
            if isinstance(reference, dict) and reference.get("url"):
                return reference.get("url", "")

    return ""

# Lecture de la clé NVD dans le .env.
def get_raw_nvd_api_key():
    return os.getenv("NVD_API_KEY", "").strip()

# Détection d’un blocage ou rate limit NVD.
def is_nvd_rate_limited(status_code, response_text):
    response_text = response_text or ""
    response_text_lower = response_text.lower()

    return (
        status_code == 429
        or "error 1015" in response_text_lower
        or "you are being rate limited" in response_text_lower
        or "temporarily banned" in response_text_lower
        or "rate limited" in response_text_lower
    )

# Détection d’une clé NVD invalide.
def is_nvd_api_key_invalid(status_code, response_text):
    response_text = (response_text or "").lower()

    if is_nvd_rate_limited(status_code, response_text):
        return False

    return (
        status_code in [401, 403]
        or "invalid api key" in response_text
        or "invalid apikey" in response_text
        or "api key is invalid" in response_text
    )

# Helper NVD/EPSS.
def get_nvd_rate_limit_sleep():
    try:
        return int(os.getenv("NVD_RATE_LIMIT_SLEEP", "90"))
    except ValueError:
        return 90

# Pause entre les requêtes NVD.
def wait_before_nvd_request(use_api_key=False):
    global NVD_LAST_REQUEST_AT

    if use_api_key:
        default_delay = os.getenv("NVD_MIN_DELAY_WITH_KEY", "1.2")
    else:
        default_delay = os.getenv("NVD_MIN_DELAY_NO_KEY", "7")

    try:
        min_delay = float(default_delay)
    except ValueError:
        min_delay = 1.2 if use_api_key else 7

    elapsed = time.time() - NVD_LAST_REQUEST_AT

    if elapsed < min_delay:
        time.sleep(min_delay - elapsed)

    NVD_LAST_REQUEST_AT = time.time()

# Vérification de la clé NVD au démarrage.
def validate_nvd_api_key(force=False):
    global NVD_API_KEY_STATUS

    api_key = get_raw_nvd_api_key()

    if not api_key:
        NVD_API_KEY_STATUS = {
            "checked": True,
            "key": None,
            "status": "missing",
            "message": "Aucune clé NVD configurée. Utilisation du mode sans clé."
        }
        print("[*] NVD : aucune clé API configurée, mode sans clé.")
        return NVD_API_KEY_STATUS

    if (
        NVD_API_KEY_STATUS.get("checked")
        and NVD_API_KEY_STATUS.get("key") == api_key
        and not force
    ):
        return NVD_API_KEY_STATUS

    validation_cve = os.getenv("NVD_VALIDATION_CVE", "CVE-2024-6387").strip()
    nvd_url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={validation_cve}"

    headers = {
        "User-Agent": "opentools-auditable/1.0",
        "Accept": "application/json",
        "apiKey": api_key
    }

    try:
        print("[*] Vérification de la clé API NVD...")

        wait_before_nvd_request(use_api_key=True)

        r = requests.get(
            nvd_url,
            headers=headers,
            timeout=20
        )

        response_text = safe_response_text(r)

        if r.status_code == 200:
            payload = r.json()
            vulnerabilities = payload.get("vulnerabilities", [])

            if vulnerabilities:
                NVD_API_KEY_STATUS = {
                    "checked": True,
                    "key": api_key,
                    "status": "valid",
                    "message": "Clé API NVD valide."
                }
                print("[+] NVD : clé API valide.")
                return NVD_API_KEY_STATUS

            NVD_API_KEY_STATUS = {
                "checked": True,
                "key": api_key,
                "status": "unknown",
                "message": "Réponse NVD 200 mais aucune vulnérabilité retournée pendant le test."
            }
            print("[!] NVD : clé API probablement valide, mais réponse de test inattendue.")
            return NVD_API_KEY_STATUS

        if is_nvd_rate_limited(r.status_code, response_text):
            NVD_API_KEY_STATUS = {
                "checked": True,
                "key": api_key,
                "status": "rate_limited",
                "message": "NVD/Cloudflare limite actuellement les requêtes. La clé n'est pas considérée invalide."
            }
            print("[!] NVD : rate limit pendant la vérification. Clé conservée.")
            return NVD_API_KEY_STATUS

        if is_nvd_api_key_invalid(r.status_code, response_text):
            NVD_API_KEY_STATUS = {
                "checked": True,
                "key": api_key,
                "status": "invalid",
                "message": "Clé API NVD invalide. Fallback en mode sans clé."
            }
            print("[!] NVD : clé API invalide. Fallback sans clé.")
            return NVD_API_KEY_STATUS

        NVD_API_KEY_STATUS = {
            "checked": True,
            "key": api_key,
            "status": "unknown",
            "message": f"Impossible de valider clairement la clé NVD. HTTP {r.status_code}."
        }
        print(f"[!] NVD : statut de clé inconnu. HTTP {r.status_code}.")
        return NVD_API_KEY_STATUS

    except Exception as e:
        NVD_API_KEY_STATUS = {
            "checked": True,
            "key": api_key,
            "status": "unknown",
            "message": f"Erreur pendant la vérification NVD : {e}"
        }
        print(f"[!] NVD : erreur pendant la vérification de la clé : {e}")
        return NVD_API_KEY_STATUS

# Helper NVD/EPSS.
def should_use_nvd_api_key():
    api_key = get_raw_nvd_api_key()

    if not api_key:
        return False

    status = validate_nvd_api_key().get("status")

    # Si rate limit ou statut inconnu, on ne marque pas la clé comme invalide.
    # Repasser sans clé réduirait encore plus la limite.
    return status in ["valid", "rate_limited", "unknown"]

# Helper NVD/EPSS.
def get_nvd_headers():
    headers = {
        "User-Agent": "opentools-auditable/1.0",
        "Accept": "application/json"
    }

    api_key = get_raw_nvd_api_key()

    if api_key and should_use_nvd_api_key():
        headers["apiKey"] = api_key

    return headers

# Helper NVD/EPSS.
def mark_nvd_api_key_invalid():
    global NVD_API_KEY_STATUS

    api_key = get_raw_nvd_api_key()

    NVD_API_KEY_STATUS = {
        "checked": True,
        "key": api_key,
        "status": "invalid",
        "message": "Clé API NVD marquée invalide après erreur API."
    }

# Récupération des détails CVE depuis NVD.
def fetch_cve_details(cve_id, cursor=None, list_ip_id=None):
    nvd_url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"

    nvd_data = {}

    for attempt in range(1, 4):
        try:
            headers = get_nvd_headers()
            use_api_key = "apiKey" in headers

            wait_before_nvd_request(use_api_key=use_api_key)

            r = requests.get(
                nvd_url,
                headers=headers,
                timeout=20
            )
            response_text = safe_response_text(r)

            if is_nvd_api_key_invalid(r.status_code, response_text) and use_api_key:
                print(f"[!] Clé API NVD invalide détectée pour {cve_id}. Nouvelle tentative sans clé.")
                mark_nvd_api_key_invalid()

                headers = {
                    "User-Agent": "opentools-auditable/1.0",
                    "Accept": "application/json"
                }

                wait_before_nvd_request(use_api_key=False)

                r = requests.get(
                    nvd_url,
                    headers=headers,
                    timeout=20
                )
                response_text = safe_response_text(r)

            if cursor is not None and list_ip_id is not None:
                log_site_response(cursor, "log_ndv", list_ip_id, nvd_url, response_text, report_tool="ndv")

            if is_nvd_rate_limited(r.status_code, response_text):
                wait_time = get_nvd_rate_limit_sleep()
                print(
                    f"[!] NVD rate limit pour {cve_id} "
                    f"(HTTP {r.status_code}, tentative {attempt}/3). "
                    f"Pause {wait_time}s."
                )
                time.sleep(wait_time)
                continue

            if r.status_code != 200:
                print(f"[!] NVD HTTP {r.status_code} pour {cve_id}")
                return {}

            vulns = r.json().get("vulnerabilities", [])
            if not vulns:
                print(f"[!] Aucune donnée NVD pour {cve_id}")
                return {}

            v = vulns[0]["cve"]

            description = ""
            descriptions = v.get("descriptions", [])
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break
            if not description and descriptions:
                description = descriptions[0].get("value", "")

            cvss = ""
            criticity = None
            risk = ""
            metrics = v.get("metrics", {})

            for metric_key in ["cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                if metrics.get(metric_key):
                    metric = metrics[metric_key][0]
                    cvss_data = metric.get("cvssData", {})
                    cvss = cvss_data.get("vectorString", "")
                    criticity = cvss_data.get("baseScore")
                    risk = (
                        metric.get("baseSeverity")
                        or cvss_data.get("baseSeverity")
                        or risk_from_score(criticity)
                    )
                    break

            cwe = ""
            for weakness in v.get("weaknesses", []):
                for weakness_desc in weakness.get("description", []):
                    value = weakness_desc.get("value", "")
                    if value and value not in ["NVD-CWE-noinfo", "NVD-CWE-Other"]:
                        cwe = value
                        break
                if cwe:
                    break

            remediation = ""

            external_link = extract_first_reference_url(v)

            nvd_data = {
                "vulnerability_name": cve_id,
                "description": description,
                "cvss": cvss,
                "criticity": criticity,
                "risk": risk,
                "cwe": cwe,
                "remediation": remediation,
                "source": "NVD",
                "external_link": external_link,
            }

            return nvd_data

        except Exception as e:
            error_text = f"Erreur NVD pour {cve_id}: {e}"
            print(f"[!] {error_text}")
            if cursor is not None and list_ip_id is not None:
                try:
                    log_site_response(cursor, "log_ndv", list_ip_id, nvd_url, error_text, report_tool="ndv")
                except Exception as log_error:
                    print(f"[!] Impossible de logger l'erreur NVD : {log_error}")
            time.sleep(5)

    return nvd_data

# Récupération du score EPSS.
def update_epss_for_cve(cursor, cve_id, list_ip_id=None):
    epss_url = f"https://vulnerability.circl.lu/api/epss/{cve_id}"

    try:
        r = requests.get(epss_url, timeout=10)
        response_text = safe_response_text(r)

        if list_ip_id is not None:
            log_site_response(cursor, "log_circl", list_ip_id, epss_url, response_text, report_tool="circl")

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
        error_text = f"Erreur EPSS pour {cve_id}: {e}"
        print(f"[!] {error_text}")
        if list_ip_id is not None:
            log_site_response(cursor, "log_circl", list_ip_id, epss_url, error_text, report_tool="circl")
        return False

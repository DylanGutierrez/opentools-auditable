"""Traduction locale des descriptions de vulnérabilités avec Ollama/TranslateGemma."""
import os
import shutil
import subprocess
import time
from datetime import datetime

import requests

from database import get_db_connection


LANGUAGES = {
    "fr": "français",
    "francais": "français",
    "français": "français",
    "en": "anglais",
    "english": "anglais",
    "anglais": "anglais",
    "es": "espagnol",
    "spanish": "espagnol",
    "espagnol": "espagnol",
    "it": "italien",
    "italian": "italien",
    "italien": "italien",
}


def get_translation_model():
    """Modèle TranslateGemma configuré."""
    return os.getenv("TRANSLATEGEMMA_MODEL", "translategemma:4b").strip() or "translategemma:4b"


def get_ollama_host():
    """Adresse locale de l'API Ollama."""
    return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip().rstrip("/")


def get_ollama_models_dir():
    """Dossier des modèles Ollama utilisé par l'installation Auditable."""
    return os.getenv("OLLAMA_MODELS_DIR", "/var/lib/auditable/ollama-models").strip()


def get_timeout():
    """Timeout large car la traduction locale peut être lente en CPU."""
    try:
        return int(os.getenv("TRANSLATEGEMMA_TIMEOUT", "240"))
    except ValueError:
        return 240


def normalize_language(value):
    """Vérification de la langue demandée."""
    key = str(value or "").strip().lower()
    if not key:
        key = "fr"
    if key not in LANGUAGES:
        raise ValueError("Langue non autorisée. Choisis : français, anglais, espagnol ou italien.")
    return LANGUAGES[key]


def start_ollama_if_possible():
    """Démarrage d'Ollama si le service est installé."""
    if shutil.which("ollama") is None:
        return False

    env = os.environ.copy()
    env.setdefault("OLLAMA_MODELS", get_ollama_models_dir())
    env.setdefault("OLLAMA_HOST", "127.0.0.1:11434")

    # Démarrage via systemd quand il est disponible.
    if shutil.which("systemctl"):
        subprocess.run(["systemctl", "start", "ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Petite attente pour laisser l'API locale répondre.
    for _ in range(20):
        try:
            response = requests.get(f"{get_ollama_host()}/api/tags", timeout=3)
            if response.status_code == 200:
                return True
        except Exception:
            time.sleep(1)

    # Fallback si le service systemd ne répond pas.
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
    except Exception:
        return False

    for _ in range(25):
        try:
            response = requests.get(f"{get_ollama_host()}/api/tags", timeout=3)
            if response.status_code == 200:
                return True
        except Exception:
            time.sleep(1)

    return False

def get_ollama_models():
    """Liste les modèles installés localement dans Ollama."""
    response = requests.get(f"{get_ollama_host()}/api/tags", timeout=10)
    response.raise_for_status()
    payload = response.json()
    return [item.get("name", "") for item in payload.get("models", [])]


def translation_status():
    """Statut utilisé par le frontend pour savoir si la traduction est prête."""
    model = get_translation_model()

    if shutil.which("ollama") is None:
        return {
            "ready": False,
            "installed": False,
            "model": model,
            "message": "Ollama n'est pas installé. Relance make install.",
        }

    if not start_ollama_if_possible():
        return {
            "ready": False,
            "installed": True,
            "model": model,
            "message": "Ollama est installé mais l'API locale ne répond pas.",
        }

    try:
        models = get_ollama_models()
    except Exception as exc:
        return {
            "ready": False,
            "installed": True,
            "model": model,
            "message": f"Impossible de lire les modèles Ollama : {exc}",
        }

    model_ready = model in models
    return {
        "ready": model_ready,
        "installed": True,
        "model": model,
        "models": models,
        "message": "TranslateGemma est prêt." if model_ready else "Modèle TranslateGemma absent. Relance make install.",
    }


def build_translation_prompt(text, target_language):
    """Préparation du prompt imposé pour éviter les commentaires du modèle."""
    return (
        "Traduit simplement ce texte, sans faire d'introduction ou de commentaire.\n"
        "Donne juste la traduction de manière formelle.\n"
        f"Langue cible : {target_language}.\n\n"
        "Texte à traduire :\n"
        f"{text}"
    )


def translate_text(text, target_language):
    """Traduction d'un texte via l'API locale Ollama."""
    model = get_translation_model()
    payload = {
        "model": model,
        "prompt": build_translation_prompt(text, target_language),
        "stream": False,
        "keep_alive": "5m",
        "options": {
            "temperature": 0.1,
            "num_predict": 4096,
        },
    }

    response = requests.post(
        f"{get_ollama_host()}/api/generate",
        json=payload,
        timeout=get_timeout(),
    )
    response.raise_for_status()
    translated = (response.json().get("response") or "").strip()
    return translated


def stop_translation_model():
    """Arrêt du modèle après la traduction pour libérer la RAM."""
    model = get_translation_model()
    if shutil.which("ollama") is None:
        return
    subprocess.run(["ollama", "stop", model], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def translate_vulnerability_descriptions(audit_id, language, force=False):
    """Traduit une par une les descriptions des vulnérabilités de l'audit."""
    target_language = normalize_language(language)
    status = translation_status()

    if not status.get("ready"):
        raise RuntimeError(status.get("message") or "TranslateGemma n'est pas prêt.")

    conn = None
    cursor = None
    translated_count = 0
    skipped_count = 0
    errors = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                v.id,
                v.CVE,
                v.description,
                v.traducted_description,
                v.traducted_language
            FROM vulnerabilities v
            INNER JOIN list_ip li ON li.id = v.ip_id
            INNER JOIN convention conv ON conv.id = li.convention_id
            WHERE conv.audit_id = %s
              AND v.description IS NOT NULL
              AND TRIM(v.description) <> ''
            ORDER BY v.id ASC
            """,
            (audit_id,)
        )
        rows = cursor.fetchall()

        for row in rows:
            current_translation = row.get("traducted_description")
            current_language = row.get("traducted_language")

            # Ne retraduit pas inutilement si la bonne langue est déjà présente.
            if current_translation and current_language == target_language and not force:
                skipped_count += 1
                continue

            try:
                translated = translate_text(row.get("description") or "", target_language)
                cursor.execute(
                    """
                    UPDATE vulnerabilities
                    SET traducted_description = %s,
                        traducted_language = %s,
                        traducted_at = %s
                    WHERE id = %s
                    """,
                    (translated or None, target_language, datetime.now(), row["id"])
                )
                conn.commit()
                translated_count += 1
            except Exception as exc:
                conn.rollback()
                errors.append({
                    "id": row.get("id"),
                    "CVE": row.get("CVE"),
                    "error": str(exc),
                })

        return {
            "audit_id": audit_id,
            "language": target_language,
            "model": get_translation_model(),
            "total": len(rows),
            "translated": translated_count,
            "skipped": skipped_count,
            "errors": errors,
        }

    finally:
        stop_translation_model()
        if cursor:
            cursor.close()
        if conn:
            conn.close()

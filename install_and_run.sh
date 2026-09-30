#!/bin/bash

set -e

PROJECT_DIR="$(pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

ENV_FILE="$BACKEND_DIR/.env"
SCHEMA_FILE="$BACKEND_DIR/schema.sql"

BACKEND_LOG="$PROJECT_DIR/backend.log"
FRONTEND_LOG="$PROJECT_DIR/frontend.log"

if [ "$EUID" -ne 0 ]; then
  echo "[!] Lance ce script en root : sudo ./install_and_run.sh"
  exit 1
fi

if [ ! -d "$BACKEND_DIR" ]; then
  echo "[!] Dossier backend introuvable : $BACKEND_DIR"
  exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "[!] Dossier frontend introuvable : $FRONTEND_DIR"
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "[!] Fichier .env introuvable : $ENV_FILE"
  exit 1
fi

if [ ! -f "$SCHEMA_FILE" ]; then
  echo "[!] Fichier schema.sql introuvable : $SCHEMA_FILE"
  exit 1
fi

get_env_value() {
  local key="$1"
  local default_value="$2"
  local value

  value="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d '=' -f2- || true)"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"

  if [ -z "$value" ]; then
    echo "$default_value"
  else
    echo "$value"
  fi
}

sql_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

get_app_user() {
  if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
    echo "$SUDO_USER"
  else
    logname 2>/dev/null || echo "root"
  fi
}

check_free_space_mb() {
  local directory="$1"
  mkdir -p "$directory"
  df -Pm "$directory" | awk 'NR==2 {print $4}'
}

configure_ollama_service() {
  local models_dir="$1"

  mkdir -p "$models_dir"

  # Le service Ollama tourne généralement avec l'utilisateur système "ollama".
  # On utilise /var/lib/auditable par défaut pour éviter les problèmes de droits
  # quand le projet est dans /home/dylan.
  if id ollama >/dev/null 2>&1; then
    chown -R ollama:ollama "$models_dir" || true
    chmod 755 /var/lib/auditable 2>/dev/null || true
    chmod -R u+rwX,g+rwX,o-rwx "$models_dir" || true
  fi

  if command -v systemctl >/dev/null 2>&1; then
    mkdir -p /etc/systemd/system/ollama.service.d
    cat > /etc/systemd/system/ollama.service.d/auditable.conf <<EOF
[Service]
Environment="OLLAMA_MODELS=$models_dir"
Environment="OLLAMA_HOST=127.0.0.1:11434"
EOF
    systemctl daemon-reload || true
    systemctl enable ollama >/dev/null 2>&1 || true
    systemctl reset-failed ollama >/dev/null 2>&1 || true
    systemctl restart ollama >/dev/null 2>&1 || systemctl start ollama >/dev/null 2>&1 || true
  else
    export OLLAMA_MODELS="$models_dir"
    export OLLAMA_HOST="127.0.0.1:11434"
    nohup ollama serve >/tmp/auditable-ollama.log 2>&1 &
  fi
}

start_ollama_fallback() {
  local models_dir="$1"

  echo "[!] Démarrage systemd Ollama non disponible ou API muette. Tentative fallback local..."
  if command -v systemctl >/dev/null 2>&1; then
    systemctl stop ollama >/dev/null 2>&1 || true
  fi
  pkill -f "ollama serve" >/dev/null 2>&1 || true
  sleep 2

  OLLAMA_MODELS="$models_dir" \
  OLLAMA_HOST="127.0.0.1:11434" \
  nohup ollama serve >/tmp/auditable-ollama.log 2>&1 &
}

show_ollama_diagnostics() {
  echo ""
  echo "[!] Diagnostics Ollama :"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl status ollama --no-pager -l 2>/dev/null || true
    echo ""
    journalctl -u ollama -n 60 --no-pager 2>/dev/null || true
  fi
  echo ""
  echo "[!] Log fallback éventuel :"
  tail -n 80 /tmp/auditable-ollama.log 2>/dev/null || true
}

wait_for_ollama() {
  local models_dir="$1"

  for i in $(seq 1 45); do
    if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
      echo "[+] Ollama est prêt."
      return 0
    fi
    sleep 1
  done

  start_ollama_fallback "$models_dir"

  for i in $(seq 1 45); do
    if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
      echo "[+] Ollama est prêt avec le fallback local."
      return 0
    fi
    sleep 1
  done

  echo "[!] Ollama ne répond pas sur http://127.0.0.1:11434"
  show_ollama_diagnostics
  return 1
}

install_translategemma() {
  local app_user
  local app_home
  local models_dir
  local free_mb

  app_user="$(get_app_user)"
  app_home="$(getent passwd "$app_user" | cut -d: -f6)"
  models_dir="${OLLAMA_MODELS_DIR:-/var/lib/auditable/ollama-models}"

  echo "[+] Installation / vérification d'Ollama pour TranslateGemma..."

  if ! command -v ollama >/dev/null 2>&1; then
    curl -fsSL https://ollama.com/install.sh | sh
  else
    echo "[+] Ollama est déjà installé."
  fi

  mkdir -p "$models_dir"
  free_mb="$(check_free_space_mb "$models_dir")"

  if [ "$free_mb" -lt "$TRANSLATEGEMMA_MIN_FREE_MB" ]; then
    echo "[!] Espace insuffisant pour TranslateGemma."
    echo "    Dossier modèles : $models_dir"
    echo "    Espace libre : ${free_mb} Mo"
    echo "    Minimum conseillé : ${TRANSLATEGEMMA_MIN_FREE_MB} Mo"
    echo ""
    echo "    Solution : libère de l'espace ou relance avec :"
    echo "    OLLAMA_MODELS_DIR=/chemin/avec/de-la-place sudo make install"
    exit 1
  fi

  configure_ollama_service "$models_dir"
  wait_for_ollama "$models_dir"

  echo "[+] Nettoyage des téléchargements Ollama incomplets éventuels..."
  find "$models_dir" -name '*-partial' -type f -delete 2>/dev/null || true
  find /usr/share/ollama/.ollama/models -name '*-partial' -type f -delete 2>/dev/null || true

  echo "[+] Téléchargement du modèle : $TRANSLATEGEMMA_MODEL"
  if ollama list | awk 'NR>1 {print $1}' | grep -Fxq "$TRANSLATEGEMMA_MODEL"; then
    echo "[+] Le modèle $TRANSLATEGEMMA_MODEL est déjà installé."
  else
    ollama pull "$TRANSLATEGEMMA_MODEL"
  fi

  echo "[+] Test rapide TranslateGemma..."
  ollama run "$TRANSLATEGEMMA_MODEL" "Traduit simplement ce texte en français, sans commentaire : hello" >/dev/null || {
    echo "[!] Le test TranslateGemma a échoué."
    exit 1
  }

  ollama stop "$TRANSLATEGEMMA_MODEL" >/dev/null 2>&1 || true
  echo "[+] TranslateGemma est installé et fonctionnel."
}

DB_HOST="$(get_env_value DB_HOST 127.0.0.1)"
DB_USER="$(get_env_value DB_USER auditable)"
DB_PASS="$(get_env_value DB_PASS admin1auditable)"
DB_NAME="$(get_env_value DB_NAME opentools_auditable)"
TRANSLATEGEMMA_MODEL="$(get_env_value TRANSLATEGEMMA_MODEL translategemma:4b)"
TRANSLATEGEMMA_MIN_FREE_MB="${TRANSLATEGEMMA_MIN_FREE_MB:-7000}"

DB_USER_SQL="$(sql_escape "$DB_USER")"
DB_PASS_SQL="$(sql_escape "$DB_PASS")"
DB_NAME_SQL="$(sql_escape "$DB_NAME")"

echo "[+] Mise à jour Kali..."
apt update

echo "[+] Installation des dépendances système..."
apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  python3-full \
  python3-dev \
  build-essential \
  curl \
  git \
  ca-certificates \
  nodejs \
  npm \
  mariadb-server \
  mariadb-client \
  nmap

echo "[+] Installation optionnelle des outils d'audit Kali..."
for pkg in nikto wpscan nuclei; do
  apt install -y "$pkg" || echo "[!] Paquet optionnel non installé ou indisponible : $pkg"
done

install_translategemma

echo "[+] Versions installées :"
python3 --version
node -v
npm -v
mysql --version

echo "[+] Démarrage de MariaDB/MySQL..."

if command -v systemctl >/dev/null 2>&1; then
  systemctl enable mariadb >/dev/null 2>&1 || true
  systemctl start mariadb || systemctl start mysql
else
  service mariadb start || service mysql start
fi

echo "[+] Attente du démarrage de la base..."
for i in $(seq 1 30); do
  if mysqladmin ping --silent >/dev/null 2>&1; then
    echo "[+] MariaDB/MySQL est prêt."
    break
  fi

  if [ "$i" -eq 30 ]; then
    echo "[!] MariaDB/MySQL ne répond pas."
    exit 1
  fi

  sleep 1
done

echo "[+] Création de la base et de l'utilisateur applicatif..."

MYSQL_BOOTSTRAP_FILE="$(mktemp)"

cat > "$MYSQL_BOOTSTRAP_FILE" <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME_SQL}\`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '${DB_USER_SQL}'@'localhost'
  IDENTIFIED BY '${DB_PASS_SQL}';

CREATE USER IF NOT EXISTS '${DB_USER_SQL}'@'127.0.0.1'
  IDENTIFIED BY '${DB_PASS_SQL}';

GRANT ALL PRIVILEGES ON \`${DB_NAME_SQL}\`.* TO '${DB_USER_SQL}'@'localhost';
GRANT ALL PRIVILEGES ON \`${DB_NAME_SQL}\`.* TO '${DB_USER_SQL}'@'127.0.0.1';

FLUSH PRIVILEGES;
SQL

mysql -u root < "$MYSQL_BOOTSTRAP_FILE"
rm -f "$MYSQL_BOOTSTRAP_FILE"

echo "[+] Import du schema.sql..."
mysql -u root < "$SCHEMA_FILE"

echo "[+] Application des migrations nécessaires au backend..."

mysql -u root "$DB_NAME" <<SQL
SET @sql := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE list_ip ADD COLUMN true_cmd_port TEXT',
    'SELECT "Colonne true_cmd_port déjà présente"'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'list_ip'
    AND COLUMN_NAME = 'true_cmd_port'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE vulnerabilities ADD COLUMN traducted_description LONGTEXT DEFAULT NULL',
    'SELECT "Colonne traducted_description déjà présente"'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'vulnerabilities'
    AND COLUMN_NAME = 'traducted_description'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE vulnerabilities ADD COLUMN traducted_language VARCHAR(32) DEFAULT NULL',
    'SELECT "Colonne traducted_language déjà présente"'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'vulnerabilities'
    AND COLUMN_NAME = 'traducted_language'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE vulnerabilities ADD COLUMN traducted_at DATETIME DEFAULT NULL',
    'SELECT "Colonne traducted_at déjà présente"'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'vulnerabilities'
    AND COLUMN_NAME = 'traducted_at'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
SQL

echo "[+] Test de connexion avec l'utilisateur applicatif..."
MYSQL_PWD="$DB_PASS" mysql -h "$DB_HOST" -u "$DB_USER" "$DB_NAME" -e "SHOW TABLES;" >/dev/null

echo "[+] Configuration du backend Python..."

cd "$BACKEND_DIR"

# Création propre du venv backend.
# On supprime l'ancien venv pour éviter un pip cassé ou rattaché au Python système.
rm -rf venv
python3 -m venv venv

VENV_PYTHON="$BACKEND_DIR/venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "[!] Impossible de créer le venv Python backend."
  exit 1
fi

# Installation de pip dans le venv si nécessaire.
# Important : on n'appelle jamais le pip système pour éviter l'erreur PEP 668.
"$VENV_PYTHON" -m ensurepip --upgrade >/dev/null 2>&1 || true

if ! "$VENV_PYTHON" -m pip --version >/dev/null 2>&1; then
  echo "[!] pip est absent du venv backend. Installe python3-full puis relance make install."
  echo "    Commande : apt install -y python3-full python3-venv"
  exit 1
fi

"$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
  "$VENV_PYTHON" -m pip install -r requirements.txt
else
  "$VENV_PYTHON" -m pip install \
    Flask \
    flask-cors \
    python-dotenv \
    mysql-connector-python \
    requests
fi

echo "[+] Configuration du frontend React..."

cd "$FRONTEND_DIR"

if [ ! -f "package.json" ]; then
  echo "[!] Aucun package.json trouvé dans $FRONTEND_DIR"
  exit 1
fi

# Nettoyage des anciennes dépendances React pour éviter les conflits npm ERESOLVE.
# Exemple : ancienne version react-i18next déjà présente dans node_modules.
echo "[+] Nettoyage des dépendances frontend précédentes..."
rm -rf node_modules
rm -f package-lock.json npm-shrinkwrap.json
npm cache verify >/dev/null 2>&1 || true

# Installation frontend tolérante aux anciens conflits de peer dependencies npm.
echo "[+] Installation des dépendances frontend..."
npm install --legacy-peer-deps

echo "[+] Lancement automatique du backend..."

cd "$BACKEND_DIR"

nohup "$BACKEND_DIR/venv/bin/python" -c "from app import app; app.run(host='0.0.0.0', port=5000, debug=False)" > "$BACKEND_LOG" 2>&1 &

BACKEND_PID=$!
echo "$BACKEND_PID" > "$PROJECT_DIR/backend.pid"

sleep 3

if ps -p "$BACKEND_PID" >/dev/null 2>&1; then
  echo "[+] Backend lancé avec le PID : $BACKEND_PID"
else
  echo "[!] Le backend semble avoir échoué. Logs :"
  tail -n 80 "$BACKEND_LOG"
  exit 1
fi

echo "[+] Lancement automatique du frontend..."

cd "$FRONTEND_DIR"

if grep -q '"dev"' package.json; then
  nohup npm run dev -- --host 0.0.0.0 > "$FRONTEND_LOG" 2>&1 &
else
  nohup npm start > "$FRONTEND_LOG" 2>&1 &
fi

FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$PROJECT_DIR/frontend.pid"

sleep 3

if ps -p "$FRONTEND_PID" >/dev/null 2>&1; then
  echo "[+] Frontend lancé avec le PID : $FRONTEND_PID"
else
  echo "[!] Le frontend semble avoir échoué. Logs :"
  tail -n 80 "$FRONTEND_LOG"
  exit 1
fi

echo ""
echo "[✓] Installation terminée et application lancée."
echo ""
echo "Backend :"
echo "  http://127.0.0.1:5000"
echo ""
echo "Frontend :"
echo "  http://127.0.0.1:5173"
echo "  ou http://127.0.0.1:3000 selon ton projet React"
echo ""
echo "Logs backend :"
echo "  tail -f $BACKEND_LOG"
echo ""
echo "Logs frontend :"
echo "  tail -f $FRONTEND_LOG"
echo ""
echo "Arrêter l'application :"
echo "  kill \$(cat $PROJECT_DIR/backend.pid) \$(cat $PROJECT_DIR/frontend.pid)"

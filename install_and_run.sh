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

DB_HOST="$(get_env_value DB_HOST 127.0.0.1)"
DB_USER="$(get_env_value DB_USER auditable)"
DB_PASS="$(get_env_value DB_PASS admin1auditable)"
DB_NAME="$(get_env_value DB_NAME opentools_auditable)"

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
SQL

echo "[+] Test de connexion avec l'utilisateur applicatif..."
MYSQL_PWD="$DB_PASS" mysql -h "$DB_HOST" -u "$DB_USER" "$DB_NAME" -e "SHOW TABLES;" >/dev/null

echo "[+] Configuration du backend Python..."

cd "$BACKEND_DIR"

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  pip install \
    Flask \
    flask-cors \
    python-dotenv \
    mysql-connector-python \
    requests
fi

deactivate

echo "[+] Configuration du frontend React..."

cd "$FRONTEND_DIR"

if [ ! -f "package.json" ]; then
  echo "[!] Aucun package.json trouvé dans $FRONTEND_DIR"
  exit 1
fi

npm install

npm install \
  react \
  react-dom \
  react-router-dom \
  axios \
  i18next \
  react-i18next \
  react-toastify \
  driver.js

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

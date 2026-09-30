#!/bin/bash

set -e

PROJECT_DIR="$(pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

ENV_FILE="$BACKEND_DIR/.env"

BACKEND_PID_FILE="$PROJECT_DIR/backend.pid"
FRONTEND_PID_FILE="$PROJECT_DIR/frontend.pid"

BACKEND_LOG="$PROJECT_DIR/backend.log"
FRONTEND_LOG="$PROJECT_DIR/frontend.log"

# Mettre à 1 si tu veux aussi supprimer /var/lib/mysql.
# Attention : cela supprime toutes les bases MariaDB/MySQL locales.
REMOVE_MYSQL_DATA=0

if [ "$EUID" -ne 0 ]; then
  echo "[!] Lance ce script en root : sudo ./uninstall_all.sh"
  exit 1
fi

echo ""
echo "[!] Ce script va désinstaller les dépendances du projet."
echo "[!] Il ne supprimera pas python3."
echo "[!] Il peut supprimer MariaDB/MySQL, Node.js, npm, make, les outils d'audit et les fichiers générés."
echo ""
read -p "Confirmer la désinstallation ? Tape OUI : " CONFIRM

if [ "$CONFIRM" != "OUI" ]; then
  echo "[!] Désinstallation annulée."
  exit 0
fi

get_env_value() {
  local key="$1"
  local default_value="$2"
  local value=""

  if [ -f "$ENV_FILE" ]; then
    value="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d '=' -f2- || true)"
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
  fi

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
DB_NAME="$(get_env_value DB_NAME opentools_auditable)"

DB_USER_SQL="$(sql_escape "$DB_USER")"
DB_NAME_SQL="$(sql_escape "$DB_NAME")"

echo "[+] Arrêt du backend..."

if [ -f "$BACKEND_PID_FILE" ]; then
  BACKEND_PID="$(cat "$BACKEND_PID_FILE")"

  if ps -p "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" 2>/dev/null || true
    sleep 1
    kill -9 "$BACKEND_PID" 2>/dev/null || true
    echo "[+] Backend arrêté : PID $BACKEND_PID"
  fi

  rm -f "$BACKEND_PID_FILE"
else
  pkill -f "from app import app" 2>/dev/null || true
  pkill -f "python app.py" 2>/dev/null || true
  pkill -f "flask run" 2>/dev/null || true
fi

echo "[+] Arrêt du frontend..."

if [ -f "$FRONTEND_PID_FILE" ]; then
  FRONTEND_PID="$(cat "$FRONTEND_PID_FILE")"

  if ps -p "$FRONTEND_PID" >/dev/null 2>&1; then
    kill "$FRONTEND_PID" 2>/dev/null || true
    sleep 1
    kill -9 "$FRONTEND_PID" 2>/dev/null || true
    echo "[+] Frontend arrêté : PID $FRONTEND_PID"
  fi

  rm -f "$FRONTEND_PID_FILE"
else
  pkill -f "npm run dev" 2>/dev/null || true
  pkill -f "npm start" 2>/dev/null || true
  pkill -f "vite" 2>/dev/null || true
  pkill -f "react-scripts start" 2>/dev/null || true
fi

echo "[+] Libération des ports utilisés par le projet..."

for PORT in 5000 5173 3000; do
  PID_ON_PORT="$(lsof -ti tcp:$PORT 2>/dev/null || true)"

  if [ -n "$PID_ON_PORT" ]; then
    echo "[+] Arrêt du processus sur le port $PORT : $PID_ON_PORT"
    kill $PID_ON_PORT 2>/dev/null || true
    sleep 1
    kill -9 $PID_ON_PORT 2>/dev/null || true
  fi
done

echo "[+] Suppression de la base de données et de l'utilisateur MySQL/MariaDB du projet..."

if command -v mysql >/dev/null 2>&1; then
  if command -v systemctl >/dev/null 2>&1; then
    systemctl start mariadb 2>/dev/null || systemctl start mysql 2>/dev/null || true
  else
    service mariadb start 2>/dev/null || service mysql start 2>/dev/null || true
  fi

  sleep 2

  MYSQL_CLEANUP_FILE="$(mktemp)"

  cat > "$MYSQL_CLEANUP_FILE" <<SQL
DROP DATABASE IF EXISTS \`${DB_NAME_SQL}\`;
DROP USER IF EXISTS '${DB_USER_SQL}'@'localhost';
DROP USER IF EXISTS '${DB_USER_SQL}'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

  mysql -u root < "$MYSQL_CLEANUP_FILE" 2>/dev/null || echo "[!] Impossible de nettoyer MySQL avec root. Nettoyage SQL ignoré."
  rm -f "$MYSQL_CLEANUP_FILE"
else
  echo "[!] Client mysql introuvable. Nettoyage SQL ignoré."
fi

echo "[+] Arrêt de MariaDB/MySQL..."

if command -v systemctl >/dev/null 2>&1; then
  systemctl stop mariadb 2>/dev/null || systemctl stop mysql 2>/dev/null || true
  systemctl disable mariadb 2>/dev/null || systemctl disable mysql 2>/dev/null || true
else
  service mariadb stop 2>/dev/null || service mysql stop 2>/dev/null || true
fi

echo "[+] Suppression des fichiers générés du projet..."

rm -f "$BACKEND_LOG" "$FRONTEND_LOG"
rm -f "$PROJECT_DIR/backend.pid" "$PROJECT_DIR/frontend.pid"

if [ -d "$BACKEND_DIR/venv" ]; then
  rm -rf "$BACKEND_DIR/venv"
  echo "[+] Environnement virtuel Python supprimé : backend/venv"
fi

if [ -d "$FRONTEND_DIR/node_modules" ]; then
  rm -rf "$FRONTEND_DIR/node_modules"
  echo "[+] node_modules supprimé : frontend/node_modules"
fi

if [ -f "$FRONTEND_DIR/package-lock.json" ]; then
  rm -f "$FRONTEND_DIR/package-lock.json"
  echo "[+] package-lock.json supprimé."
fi

echo "[+] Désinstallation des paquets système installés pour le projet..."

purge_if_installed() {
  local pkg="$1"

  if dpkg -s "$pkg" >/dev/null 2>&1; then
    echo "[+] Suppression du paquet : $pkg"
    apt purge -y "$pkg" || true
  else
    echo "[i] Paquet absent : $pkg"
  fi
}

PACKAGES_TO_PURGE=(
  nodejs
  npm
  mariadb-server
  mariadb-client
  make
  build-essential
  python3-pip
  python3-venv
  python3-dev
  nmap
  nikto
  wpscan
  nuclei
  lsof
)

for pkg in "${PACKAGES_TO_PURGE[@]}"; do
  purge_if_installed "$pkg"
done

echo "[+] Nettoyage apt..."

apt autoremove -y
apt autoclean -y

if [ "$REMOVE_MYSQL_DATA" = "1" ]; then
  echo "[!] Suppression complète des données MySQL/MariaDB locales..."
  rm -rf /var/lib/mysql
  rm -rf /etc/mysql
fi

echo ""
echo "[✓] Désinstallation terminée."
echo ""
echo "Conservé :"
echo "  - python3"
echo "  - tes fichiers source backend/frontend"
echo "  - ton app.py, .env, schema.sql, package.json"
echo ""
echo "Supprimé si présent :"
echo "  - backend/venv"
echo "  - frontend/node_modules"
echo "  - frontend/package-lock.json"
echo "  - backend.log / frontend.log"
echo "  - base ${DB_NAME}"
echo "  - utilisateur MySQL ${DB_USER}"
echo "  - Node.js, npm, MariaDB/MySQL, make et outils d'audit installés pour le projet"

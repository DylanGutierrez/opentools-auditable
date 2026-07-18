#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_LOG="$PROJECT_DIR/backend.log"
FRONTEND_LOG="$PROJECT_DIR/frontend.log"
BACKEND_PID="$PROJECT_DIR/backend.pid"
FRONTEND_PID="$PROJECT_DIR/frontend.pid"
BACKEND_PORT="${BACKEND_PORT:-5000}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"

info() { echo "[+] $*"; }
warn() { echo "[!] $*"; }

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

start_database() {
  if command_exists systemctl; then
    sudo systemctl start mariadb 2>/dev/null || sudo systemctl start mysql 2>/dev/null || true
  elif command_exists service; then
    sudo service mariadb start 2>/dev/null || sudo service mysql start 2>/dev/null || true
  fi
}

kill_stale_pid() {
  local pid_file="$1"
  local label="$2"

  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      warn "$label semble déjà lancé avec le PID $pid."
      return 0
    fi
    rm -f "$pid_file"
  fi
  return 1
}

start_backend() {
  if [ ! -d "$BACKEND_DIR" ]; then
    warn "Dossier backend introuvable : $BACKEND_DIR"
    exit 1
  fi

  if kill_stale_pid "$BACKEND_PID" "Backend"; then
    return
  fi

  local python_bin="$BACKEND_DIR/venv/bin/python"
  if [ ! -x "$python_bin" ]; then
    python_bin="$(command -v python3 || true)"
  fi

  if [ -z "$python_bin" ]; then
    warn "python3 introuvable."
    exit 1
  fi

  info "Vérification syntaxe backend..."
  (cd "$BACKEND_DIR" && "$python_bin" -m py_compile app.py)

  info "Lancement backend sur le port $BACKEND_PORT..."
  (
    cd "$BACKEND_DIR"
    nohup "$python_bin" -c "from app import app; app.run(host='0.0.0.0', port=int('$BACKEND_PORT'), debug=False)" \
      > "$BACKEND_LOG" 2>&1 &
    echo $! > "$BACKEND_PID"
  )

  sleep 2
  if ! kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then
    warn "Le backend semble avoir échoué. Logs :"
    tail -n 80 "$BACKEND_LOG" || true
    exit 1
  fi

  info "Backend lancé. Logs : $BACKEND_LOG"
}

start_frontend() {
  if [ ! -d "$FRONTEND_DIR" ]; then
    warn "Dossier frontend introuvable : $FRONTEND_DIR"
    exit 1
  fi

  if kill_stale_pid "$FRONTEND_PID" "Frontend"; then
    return
  fi

  if ! command_exists npm; then
    warn "npm introuvable. Installe nodejs/npm avant de relancer."
    exit 1
  fi

  info "Vérification dépendance frontend driver.js..."
  if [ ! -d "$FRONTEND_DIR/node_modules/driver.js" ]; then
    (cd "$FRONTEND_DIR" && npm install driver.js)
  fi

  info "Lancement frontend..."
  (
    cd "$FRONTEND_DIR"
    if npm run | grep -qE '^  start$| start$'; then
      HOST="$FRONTEND_HOST" nohup npm start > "$FRONTEND_LOG" 2>&1 &
    elif npm run | grep -qE '^  dev$| dev$'; then
      nohup npm run dev -- --host "$FRONTEND_HOST" > "$FRONTEND_LOG" 2>&1 &
    else
      warn "Aucun script npm start/dev trouvé."
      exit 1
    fi
    echo $! > "$FRONTEND_PID"
  )

  sleep 2
  if ! kill -0 "$(cat "$FRONTEND_PID")" 2>/dev/null; then
    warn "Le frontend semble avoir échoué. Logs :"
    tail -n 80 "$FRONTEND_LOG" || true
    exit 1
  fi

  info "Frontend lancé. Logs : $FRONTEND_LOG"
}

cd "$PROJECT_DIR"
start_database
start_backend
start_frontend

info "Services lancés."
info "Backend : http://127.0.0.1:$BACKEND_PORT"
info "Frontend : regarde $FRONTEND_LOG pour l'URL exacte, souvent http://localhost:3000"

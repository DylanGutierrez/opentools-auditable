#!/bin/bash

PROJECT_DIR="$(pwd)"

BACKEND_PID_FILE="$PROJECT_DIR/backend.pid"
FRONTEND_PID_FILE="$PROJECT_DIR/frontend.pid"

echo "[+] Arrêt de l'application..."

echo "[+] Arrêt du backend..."

if [ -f "$BACKEND_PID_FILE" ]; then
  BACKEND_PID="$(cat "$BACKEND_PID_FILE")"

  if ps -p "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID"
    echo "[+] Backend arrêté : PID $BACKEND_PID"
  else
    echo "[!] Aucun backend actif avec le PID $BACKEND_PID"
  fi

  rm -f "$BACKEND_PID_FILE"
else
  echo "[!] Fichier backend.pid introuvable."
  echo "[+] Tentative d'arrêt par recherche de processus Flask/Python..."
  pkill -f "app.py" 2>/dev/null || true
  pkill -f "app.run" 2>/dev/null || true
fi

echo "[+] Arrêt du frontend..."

if [ -f "$FRONTEND_PID_FILE" ]; then
  FRONTEND_PID="$(cat "$FRONTEND_PID_FILE")"

  if ps -p "$FRONTEND_PID" >/dev/null 2>&1; then
    kill "$FRONTEND_PID"
    echo "[+] Frontend arrêté : PID $FRONTEND_PID"
  else
    echo "[!] Aucun frontend actif avec le PID $FRONTEND_PID"
  fi

  rm -f "$FRONTEND_PID_FILE"
else
  echo "[!] Fichier frontend.pid introuvable."
  echo "[+] Tentative d'arrêt par recherche de processus npm/vite/react..."
  pkill -f "npm run dev" 2>/dev/null || true
  pkill -f "npm start" 2>/dev/null || true
  pkill -f "vite" 2>/dev/null || true
  pkill -f "react-scripts start" 2>/dev/null || true
fi

echo "[+] Libération éventuelle des ports 5000, 5173 et 3000..."

for PORT in 5000 5173 3000; do
  PID_ON_PORT="$(lsof -ti tcp:$PORT 2>/dev/null || true)"

  if [ -n "$PID_ON_PORT" ]; then
    echo "[+] Arrêt du processus sur le port $PORT : $PID_ON_PORT"
    kill $PID_ON_PORT 2>/dev/null || true
  fi
done

echo "[+] Arrêt de la base de données MariaDB/MySQL..."

if command -v systemctl >/dev/null 2>&1; then
  systemctl stop mariadb 2>/dev/null || systemctl stop mysql 2>/dev/null || true
else
  service mariadb stop 2>/dev/null || service mysql stop 2>/dev/null || true
fi

echo ""
echo "[✓] Backend, frontend et base de données arrêtés."

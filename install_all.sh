#!/bin/bash

set -e

PROJECT_DIR="$(pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "[+] Mise à jour des paquets Kali..."
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
  npm

echo "[+] Vérification Node.js / npm..."
node -v
npm -v

echo "[+] Configuration du backend Python..."

if [ ! -d "$BACKEND_DIR" ]; then
  echo "[!] Dossier backend introuvable : $BACKEND_DIR"
  exit 1
fi

cd "$BACKEND_DIR"

echo "[+] Création de l'environnement virtuel Python..."
python3 -m venv venv

echo "[+] Activation du venv..."
source venv/bin/activate

echo "[+] Mise à jour de pip..."
pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
  echo "[+] Installation depuis requirements.txt..."
  pip install -r requirements.txt
else
  echo "[+] Installation des dépendances backend Python..."
  pip install \
    Flask \
    flask-cors \
    python-dotenv \
    mysql-connector-python \
    requests
fi

deactivate

echo "[+] Configuration du frontend React..."

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "[!] Dossier frontend introuvable : $FRONTEND_DIR"
  exit 1
fi

cd "$FRONTEND_DIR"

if [ ! -f "package.json" ]; then
  echo "[!] Aucun package.json trouvé dans frontend."
  echo "[!] Si ton frontend React existe déjà, vérifie le chemin FRONTEND_DIR."
  exit 1
fi

echo "[+] Installation des dépendances npm existantes..."
npm install

echo "[+] Installation des bibliothèques React utilisées dans tes imports..."
npm install \
  react \
  react-dom \
  react-router-dom \
  axios \
  i18next \
  react-i18next \
  react-toastify

echo ""
echo "[✓] Installation terminée."
echo ""
echo "Pour lancer le backend :"
echo "cd $BACKEND_DIR"
echo "source venv/bin/activate"
echo "python app.py"
echo ""
echo "Pour lancer le frontend :"
echo "cd $FRONTEND_DIR"
echo "npm run dev"
echo ""
echo "Si ton projet React utilise Create React App au lieu de Vite :"
echo "npm start"

#!/bin/bash

set -e

PROJECT_DIR="$(pwd)"

echo "[+] Installation de make..."

if command -v make >/dev/null 2>&1; then
  echo "[+] make est déjà installé."
else
  if [ "$EUID" -eq 0 ]; then
    apt update
    apt install -y make
  else
    sudo apt update
    sudo apt install -y make
  fi
fi

echo "[+] Création du Makefile..."

cat > "$PROJECT_DIR/Makefile" <<'EOF'
.PHONY: help install run stop uninstall

SHELL := /bin/bash

help:
	@echo ""
	@echo "Commandes disponibles :"
	@echo ""
	@echo "  make install      Lance install_and_run.sh"
	@echo "  make run          Lance run.sh"
	@echo "  make stop         Lance stop_all.sh"
	@echo "  make uninstall    Lance uninstall_all.sh"
	@echo ""

install:
	@if [ ! -f "./install_and_run.sh" ]; then \
		echo "[!] Script introuvable : install_and_run.sh"; \
		exit 1; \
	fi
	@chmod +x ./install_and_run.sh
	@./install_and_run.sh

run:
	@if [ ! -f "./run.sh" ]; then \
		echo "[!] Script introuvable : run.sh"; \
		exit 1; \
	fi
	@chmod +x ./run.sh
	@./run.sh

stop:
	@if [ ! -f "./stop_all.sh" ]; then \
		echo "[!] Script introuvable : stop_all.sh"; \
		exit 1; \
	fi
	@chmod +x ./stop_all.sh
	@./stop_all.sh

uninstall:
	@if [ ! -f "./uninstall_all.sh" ]; then \
		echo "[!] Script introuvable : uninstall_all.sh"; \
		exit 1; \
	fi
	@chmod +x ./uninstall_all.sh
	@./uninstall_all.sh
EOF

echo "[+] Makefile créé avec succès."

echo ""
echo "[✓] Configuration terminée."
echo ""
echo "Tu peux maintenant utiliser :"
echo ""
echo "  make install"
echo "  make run"
echo "  make stop"
echo ""

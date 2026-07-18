.PHONY: help install run stop

SHELL := /bin/bash

help:
	@echo ""
	@echo "Commandes disponibles :"
	@echo ""
	@echo "  make install    Lance install_and_run.sh"
	@echo "  make run        Lance run.sh"
	@echo "  make stop       Lance stop_all.sh"
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

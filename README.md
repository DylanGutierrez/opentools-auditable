# Auditable - TranslateGemma

Version complète du projet avec backend modulaire, frontend modulaire et traduction locale via Ollama / TranslateGemma.

## Correction

Cette version corrige l'erreur npm `ERESOLVE could not resolve` rencontrée pendant `make install`. Problème survenu dans une version antérieur que je pense lié à un conflit de librairies.

Corrections appliquées :

- nettoyage automatique de "frontend/node_modules" pendant "make install".
- suppression de "package-lock.json" avant réinstallation.
- installation frontend avec "npm install --legacy-peer-deps".
- dépendance "react-i18next" alignée sur une version compatible avec le projet existant.
- "run.sh" réinstalle les dépendances frontend avec "--legacy-peer-deps" mais seulement si "node_modules" est absent.

## Installation

cd /home/dylan/Documents/opentools-auditable
sudo make install

## Lancement sans réinstallation

make run

## Arrêt

make stop

## TranslateGemma

Le script "install_and_run.sh" installe ou vérifie Ollama, télécharge "translategemma:4b", teste le modèle (pour vérifier son fonctionnement), puis lance le backend et le frontend.

La traduction se lance depuis la page "Paramètres".


## Correction 1.07

Cette version évite l'erreur Kali/Debian `externally-managed-environment`.
L'installation backend utilise maintenant uniquement "backend/venv/bin/python -m pip" et n'appelle plus le "pip" système.
Les dossiers "__pycache__" ont aussi été retirés de l'archive pour éviter les blocages de copie liés aux droits root.

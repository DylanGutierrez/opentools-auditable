# Auditable - TranslateGemma v16

Version complète du projet avec backend modulaire, frontend modulaire et traduction locale via Ollama / TranslateGemma.

## Correction v16

Cette version corrige l'erreur npm `ERESOLVE could not resolve` rencontrée pendant `make install`.

Corrections appliquées :

- nettoyage automatique de `frontend/node_modules` pendant `make install` ;
- suppression de `package-lock.json` et `npm-shrinkwrap.json` avant réinstallation ;
- installation frontend avec `npm install --legacy-peer-deps` ;
- dépendance `react-i18next` alignée sur une version compatible avec le projet existant ;
- `run.sh` réinstalle les dépendances frontend avec `--legacy-peer-deps` si `node_modules` est absent.

## Installation

```bash
cd /home/dylan/Documents/opentools-auditable
sudo make install
```

## Lancement sans réinstallation

```bash
make run
```

## Arrêt

```bash
make stop
```

## TranslateGemma

Le script `install_and_run.sh` installe ou vérifie Ollama, télécharge `translategemma:4b`, teste le modèle, puis lance le backend et le frontend.

La traduction se lance depuis la page **Paramètres**.


## Correction v17

Cette version évite l'erreur Kali/Debian `externally-managed-environment` liée à PEP 668.
L'installation backend utilise maintenant uniquement `backend/venv/bin/python -m pip` et n'appelle plus le `pip` système.
Les dossiers `__pycache__` ont aussi été retirés de l'archive pour éviter les blocages de copie liés aux droits root.

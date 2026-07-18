# Contenu actuel du github :

- Le code source, backend et frontend.
- Le pdf du Jalon T2 pour suivre l'avancement du projet.
- Pour comprendre comment utiliser Auditable, il suffit de l'installer, car il guide l'utilisateur de lui-même grâce à driver.js.

# Auditable

Nom : Auditable (par OpenTools)
Concept : Plateforme locale de penteste assisté, guidée et open source, pour démocratiser les audits de surface d’attaque.

Le projet Auditable vise à concevoir une plateforme locale de tests de pénétration assistés, destinée à démocratiser les audits de surface d’attaque au sein des organisations qui ne disposent pas d’expertise sécurité avancée. L’idée centrale est de proposer un outil installable en local, basé sur une API Python et une interface web en React, qui orchestre des outils open source de sécurité déjà existants et reconnus (Nmap, dnsenum/dnsrecon, Nikto, wpscan, Nuclei, etc.), tout en essayant de guider l’utilisateur à chaque étape (La création d’une présentation explicative de l’outil pas à pas, un peu comme le fait Google avec ses outils est à venir. Ex : Intune).

Le but de ce projet est de promouvoir l'open source et c'est pour cela qu'il a été conçu pour fonctionner uniquement sous Linux (Debian, Kali, Ubuntu). Étant donné que les outils de pentest utilisé par le backend sont tous déjà préinstallés sur Kali Linux, c'est le candidat parfait pour l'installation d'Auditable et c'est également l'OS que je préconnise d'utiliser.

# Auditable---Backend

Le backend du projet Auditable est en python. Vous pouvez installer Python si vous ne l'avez pas, mais il est aujourd'hui automatiquement préinstallé sur la grande majorité des OS Debian et Kali Linux est basé sur Débian et s'appuie énormément sur Python pour faire fonctionner une multitude d'outils de tests de pénétration et de scripts système.

1. Versions installées

Dans les versions récentes de Kali Linux :

- Python 3 est la version standard et par défaut.
- Python 2 n'est plus installé par défaut (depuis que Python 2 a atteint sa fin de vie), mais il reste disponible dans les dépôts si vous avez besoin de faire tourner de vieux outils spécifiques.

# Auditable---Frontend

Le frontend a été conçu en React JS, il vous faudra donc installer node et npm, mais ne vous inquiétez pas, des scripts Shell sont là pour automatiser l'installation (idem pour le backend). Vous devrez simplement les exécuter en tant qu'admin, car il sont necessaires pour l'installation de certains éléments.

# Installation du projet Auditable

Placez-vous dans le répertoire "opentools-auditable", la racine du projet Auditable et lancez le script d'installation "shell_frontend_install.sh" avec la commande suivante :

sudo ./shell_frontend_install.sh

Faite de même avec le backend, Placez-vous dans le répertoire "backend" du projet Auditable et lancez le script d'installation "shell_backend_install.sh" avec la commande suivante :

sudo ./shell_backend_install.sh


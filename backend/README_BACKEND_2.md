# Backend Auditable refactorisé

Cette version reprend le backend actuel sans la partie IA du à un incident technique lié au disque dur virtuel.
Le code est séparé par responsabilité : configuration, base de données, services et routes.
Ce n'est pas vraiement ce que je considère comme une véritable clean architecture, mais de mon point de vue cela offre une bonne visibilité d'ensemble.
Disons que j'ai refactorisé le backend vers une architecture modulaire inspirée de la Clean Architecture. Les routes, services, accès base de données, configuration et outils techniques sont séparés juste pour la lisibilité, la maintenance et l’évolutivité du projet.

## Structure

backend/
|── app.py
|── config.py
|── database.py
|── services/
|   |── system.py
|   |── reports.py
|   |── settings_service.py
|   |── security_feeds.py
|   |── scan_helpers.py
|── routes/
    |── config_routes.py
    |── client_routes.py
    |── convention_routes.py
    |── scope_routes.py
    |── settings_routes.py
    |── logs_routes.py
    |── audit_routes.py
    |── scan_routes.py

|---|
    |

### Rappel : Garder un niveau de commentaire potable pour s'y retrouver sans trop de difficulté

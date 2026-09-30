# Backend Auditable refactorisé

Cette version reprend le backend actuel avec la traduction locale TranslateGemma réintégrée.
Le code est séparé par responsabilité : configuration, base de données, services et routes.

## Structure


backend/
├── app.py
├── config.py
├── database.py
├── services/
│   ├── system.py
│   ├── reports.py
│   ├── settings_service.py
│   ├── security_feeds.py
│   └── scan_helpers.py
└── routes/
    ├── config_routes.py
    ├── client_routes.py
    ├── convention_routes.py
    ├── scope_routes.py
    ├── settings_routes.py
    ├── logs_routes.py
    ├── audit_routes.py
    └── scan_routes.py


Les commentaires sont volontairement simples pour expliquer les actions principales du code.

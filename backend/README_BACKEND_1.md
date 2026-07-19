# Backend Auditable refactorisé

Cette version reprend le backend actuel sans la partie IA du à un incident technique lié au disque dur virtuel.
Le code est séparé par responsabilité : configuration, base de données, services et routes.
Ce n'est pas vraiement ce que je considère comme une véritable clean architecture, mais de mon point de vue cela offre une bonne visibilité d'ensemble.
Disons que j'ai refactorisé le backend vers une architecture modulaire inspirée de la Clean Architecture. Les routes, services, accès base de données, configuration et outils techniques sont séparés juste pour la lisibilité, la maintenance et l’évolutivité du projet.

## Infomation Imporante :

Saisissez votre propre clé API NVD (cette clé est gratuite) dans le ".env". Attribuez votre clé API à la variable "NVD_API_KEY" et si votre clé API est valide, redémarez Auditable. Cela vous permettra de faire 50 requêtes API, au lieu de 5 par delai de 30 secondes.

Dans ce ".env", vous pouvez aussi personnaliser votre base de données Mysql. Je vous recommande d'ailleurs fortement de les modifier.

DB_USER=auditable
DB_PASS=admin1auditable
DB_NAME=opentools_auditable

Modifiez également la valeur "user_name" dans le ".env" et mettez votre propre nom. Vous serez dans l'obligation de le faire pour auditer vos clients.

## Structure

<img width="237" height="496" alt="image" src="https://github.com/user-attachments/assets/ee7c5fbe-d5aa-4b4e-9810-1a942d391e99" />



### Rappel : Garder un niveau de commentaire potable pour s'y retrouver sans trop de difficulté

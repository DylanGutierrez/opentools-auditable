# Refactor frontend Auditable

Cette version sépare le frontend en pages, composants, utilitaires et configuration.

Structure principale :

- "src/App.js" : routes de l'application
- "src/components/Header.js" : header commun
- "src/components/GuideButton.js" : bouton Guide Driver.js
- "src/components/ClientForm.js" : formulaire client réutilisable
- "src/pages/" : pages fonctionnelles
- "src/utils/" : fonctions partagées
- "src/config/api.js" : URL de l'API Flask

Installation en passant le dossier frontend sans utiliser la commande make (installez npm avant toutes chose):

cd /opentools-auditable/frontend

npm install

npm install \
  react \
  react-dom \
  react-router-dom \
  axios \
  i18next \
  react-i18next \
  react-toastify \
  driver.js
  
npm start


Installation en utilisant dans le dossier racine via la commande make (installe également le backend), installez make avant tout avant toutes chose):

cd opentools-auditable
sudo chmod +x setup_make.sh
make install

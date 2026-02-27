# ⚽ PredictaBall — Application Web

Interface web Vue.js pour l'algorithme de prédiction de matchs de football.

## 🗂️ Structure du projet

```
predictaball/
├── backend/
│   ├── app.py           ← API Flask (backend Python)
│   └── requirements.txt
└── frontend/
    └── index.html       ← App Vue.js (aucune compilation requise)
```

## 🚀 Lancement en 3 étapes

### 1. Installer les dépendances Python
```bash
cd backend
pip install -r requirements.txt
```

### 2. Lancer le backend Flask
```bash
cd backend
python app.py
```
> Le serveur démarre sur **http://localhost:5000**

### 3. Ouvrir l'interface
Ouvrez simplement le fichier `frontend/index.html` dans votre navigateur.

> ⚠️ Si le navigateur bloque les requêtes CORS (fichier local), lancez un mini-serveur HTTP :
> ```bash
> cd frontend
> python -m http.server 8080
> ```
> Puis ouvrez **http://localhost:8080**

## ✨ Fonctionnalités

- 🏆 Sélection du championnat (Ligue 1, PL, La Liga, Bundesliga, Serie A, CL)
- 📅 Affichage des 5 prochains matchs
- 📊 Analyse complète avec :
  - Statistiques de classement des deux équipes
  - Forme récente (5 derniers matchs)
  - Confrontations directes H2H
  - Top buteurs par équipe
  - Probabilités de victoire / nul
  - Pronostic recommandé avec indice de confiance
  - Prédiction Over/Under 2.5 buts & BTTS

## 🔑 Clé API

La clé `football-data.org` est déjà configurée dans `backend/app.py`.

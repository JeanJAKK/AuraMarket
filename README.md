# Marketplace avec Odoo

## Objectif

Plateforme web permettant :

- aux vendeurs de publier leurs produits
- aux clients de consulter et commander
- à l’admin de gérer l’ensemble

## Stack

- Backend : Odoo Community (Python, PostgreSQL)
- Frontend : Odoo Website (QWeb)
- Modules personnalisés

## Fonctionnalités

- Utilisateurs : Admin / Vendeur / Client
- Produits : CRUD, catégories, prix, images
- Vendeurs : page publique + dashboard
- Commandes : panier, paiement, historique

## Installation

```
  Corriger le submodule odoo (le mieux)
  1) *Récupérer l’URL exacte* du dépôt Odoo qu’il veut utiliser (ex: https://github.com/odoo/odoo.git ou un fork).
  2) À la racine du repo, *créer/ajouter .gitmodules* avec l’entrée :

  ini
  [submodule "odoo"]
      path = odoo
      url = <URL_DU_DEPOT_ODOO>


  3) Puis exécuter (dans son repo local) :
  bash
  git submodule sync --recursive
  git add .gitmodules
  git add odoo
  git commit -m "Fix odoo submodule configuration"
  git push


  Après ça, toi (et tout le monde) pourrez faire :
  bash
  git clone --recurse-submodules https://github.com/JeanJAKK/AuraMarket.git
  # ou si déjà cloné
  git submodule update --init --recursive
```

```
  git clone https://github.com/odoo/odoo.git
  cd odoo
  pip install -r requirements.txt
  python odoo-bin -d marketplace_db
```

## Lancer interface en ligne

```
  cd /home/jakk/Bureau/repository/MarketHub/odoo
  source ../venv/bin/activate
  python odoo-bin -d marketplace_db -u marketplace --dev=all
```

## Roadmap

- MVP : produits, vendeurs, commandes
- Phase 2 : UI/UX, interactions
- Phase 3 : commissions, paiement multi-vendeur
- Phase 4 : déployable I

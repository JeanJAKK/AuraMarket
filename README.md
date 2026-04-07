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
  git clone https://github.com/odoo/odoo.git
  cd odoo
  pip install -r requirements.txt
  python odoo-bin -d marketplace_db
```

## Lancer interface en ligne

```
  cd /home/jakk/Bureau/repository/AuraMarket/odoo
  source ../venv/bin/activate
  python odoo-bin -d marketplace_db -u marketplace --dev=all
```

## Roadmap

- MVP : produits, vendeurs, commandes
- Phase 2 : UI/UX, interactions
- Phase 3 : commissions, paiement multi-vendeur

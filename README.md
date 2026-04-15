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

Cloner le repo en récupérant automatiquement le submodule Odoo :

```bash
git clone --recurse-submodules https://github.com/JeanJAKK/AuraMarket.git
# ou si déjà cloné
git submodule update --init --recursive
```

Installer les dépendances Python :

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r odoo/requirements.txt
```

Lancer Odoo en incluant les addons custom du repo (`addons/marketplace`) :

```bash
source venv/bin/activate
python odoo/odoo-bin -d marketplace_db --addons-path=odoo/addons,odoo/odoo/addons,addons -u marketplace --dev=all
```

## Roadmap

- MVP : produits, vendeurs, commandes
- Phase 2 : UI/UX, interactions
- Phase 3 : commissions, paiement multi-vendeur
- Phase 4 : déployable I

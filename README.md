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

## Installation et exécution

### 1) Cloner le repo et récupérer Odoo

```bash
git clone --recurse-submodules https://github.com/JeanJAKK/AuraMarket.git
cd AuraMarket
# si le repo est déjà cloné sans le sous-module :
git submodule update --init --recursive
```

### 2) Créer l’environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

### 3) Installer les dépendances Odoo

```bash
pip install -r odoo/requirements.txt
```

### 4) Vérifier la base PostgreSQL

La base `marketplace_db` doit déjà exister. Si ce n’est pas le cas, créez-la avec le bon utilisateur PostgreSQL :

```bash
sudo -u postgres psql
CREATE USER odoo WITH CREATEDB PASSWORD 'odoo';
CREATE DATABASE marketplace_db OWNER odoo;
\q
```

Si la base existe déjà mais que le lancement échoue avec une erreur du type :

```text
must be owner of table product_product
```

cela signifie que la base n’est pas propriétaire du bon rôle. Il faut alors corriger la propriété :

```bash
sudo -u postgres psql -d postgres
ALTER DATABASE marketplace_db OWNER TO odoo;
GRANT ALL PRIVILEGES ON DATABASE marketplace_db TO odoo;
\q
```

### 5) Lancer le serveur Odoo

Depuis la racine du projet :

```bash
source venv/bin/activate
python odoo/odoo-bin \
  -d marketplace_db \
  --addons-path=odoo/addons,odoo/odoo/addons,addons \
  -u marketplace \
  --db_host=localhost \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=odoo \
  --dev=all
```

Le projet est ensuite accessible sur :

```text
http://localhost:8069
```

### 6) Commande de démarrage rapide

Pour un lancement simple si la base est déjà prête :

```bash
cd /home/jakk/Bureau/repository/AuraMarket
source venv/bin/activate
python odoo/odoo-bin -d marketplace_db --addons-path=odoo/addons,odoo/odoo/addons,addons -u marketplace --db_host=localhost --db_port=5432 --db_user=odoo --db_password=odoo --dev=all
```

### 7) Dépannage

- `database does not exist` : créez la base `marketplace_db`.
- `must be owner of table product_product` : changez le propriétaire de la base vers `odoo`.
- `FATAL: password authentication failed` : vérifiez le mot de passe PostgreSQL du rôle utilisé par Odoo.
- `ModuleNotFoundError` : vérifiez que le sous-module Odoo est bien présent
  (`git submodule update --init --recursive`).
- `Adresse déjà utilisée` ou `Port 8069 is in use by another program` : arrêtez le processus utilisant le port 8069 (ex. `sudo lsof -ti:8069 | xargs kill -9`) ou changez le port dans la commande de lancement.

## Roadmap

- MVP : produits, vendeurs, commandes
- Phase 2 : UI/UX, interactions
- Phase 3 : commissions, paiement multi-vendeur
- Phase 4 : déployable

# AuraMarket (Odoo 17) — Guide Windows : du clonage à l’exécution

Ce guide explique comment lancer **AuraMarket** sur **Windows**, depuis un clone Git jusqu’au démarrage d’Odoo.

Toutes les commandes ci-dessous sont prévues pour le **terminal intégré de VS Code** en profil **PowerShell**.

> Version Odoo : **17.0** (submodule `odoo/`)  
> Python requis : **>= 3.10** (recommandé : **Python 3.11 x64**)

---

## 0) Prérequis (Windows)

Installez :

- **Python 3.11 (64-bit)** (ou 3.10 minimum).
- **Git for Windows**.
- **PostgreSQL** (recommandé : 14/15/16).

Optionnel mais utile :

- **wkhtmltopdf** (pour l’impression PDF de certains rapports Odoo). Sans ça, Odoo démarre quand même.

---

## 1) Cloner le dépôt (avec le submodule Odoo)

Ouvrez VS Code, puis le **Terminal intégré** (PowerShell) dans un dossier de travail, puis :

```powershell
git clone --recurse-submodules --depth=1 --shallow-submodules https://github.com/JeanJAKK/AuraMarket.git
cd AuraMarket
```

Si vous avez déjà cloné sans submodule :

```powershell
git submodule update --init --recursive --depth=1
```

> Note : un clonage “shallow” (`--depth=1`) limite l’historique Git (plus rapide / plus léger). Si vous devez travailler avec l’historique complet d’Odoo, clonez sans `--depth`.

---

## 2) Créer un environnement virtuel (avec la bonne version Python)

Odoo 17 requiert Python **>= 3.10**. Sur Windows, le plus fiable est d’utiliser le launcher `py` pour cibler la version.

> Important : ce repo peut contenir un dossier `venv/` déjà présent (artefact). Sur Windows, **ne l’utilisez pas** : recréez toujours votre venv local.

### 2.1 Vérifier la version Python

```powershell
py --version
py -3.11 --version
```

Si `py -3.11` ne fonctionne pas, installez Python 3.11 (x64) puis réessayez.

### 2.2 Créer le venv

Depuis la racine du repo :

```powershell
py -3.11 -m venv venv
```

### 2.3 Activer le venv

PowerShell :

```powershell
.\venv\Scripts\Activate.ps1
```

Si PowerShell bloque l’activation (ExecutionPolicy), exécutez une fois :

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Puis relancez l’activation.

### 2.4 Mettre à jour `pip`

```powershell
python -m pip install --upgrade pip setuptools wheel
```

---

## 3) Installer les dépendances Python d’Odoo

Toujours avec le venv activé :

```powershell
pip install -r odoo\requirements.txt
```

Si `pip` tente de compiler des dépendances (rare avec Python 3.11), installez **Microsoft C++ Build Tools** ou basculez sur **WSL**.

---
```powershell
python -m pip uninstall setuptools -y
python -m pip install "setuptools<81"
```

## 4) Configurer PostgreSQL (création user + base)

Odoo se connecte à PostgreSQL avec un **rôle** (user) PostgreSQL.

Deux approches :

- **Approche A (recommandée)** : créer un rôle PostgreSQL `odoo` + mot de passe, et lancer Odoo avec `--db_user` / `--db_password`.
- **Approche B** : créer un rôle PostgreSQL qui correspond à votre nom d’utilisateur Windows (moins portable).

### 4.1 Approche A — créer le rôle `odoo`

Dans `psql` (ou via pgAdmin), en tant que superuser `postgres` :

```sql
CREATE USER odoo WITH CREATEDB PASSWORD 'CHANGER_MOI';
CREATE DATABASE marketplace_db OWNER odoo;
```

> Remplacez `CHANGER_MOI` par un mot de passe.

---

## 5) Lancer AuraMarket (Odoo) avec les addons custom

Depuis la racine du repo, venv activé.

### 5.1 Initialiser la base + installer le module (recommandé)

Cette commande installe le module `marketplace` (base neuve) puis s’arrête :

```powershell
python odoo\odoo-bin -d marketplace_db --addons-path=odoo/addons,odoo/odoo/addons,addons -i marketplace --stop-after-init --db_user=odoo --db_password=CHANGER_MOI
```

Si la base existe déjà et que vous voulez simplement appliquer les changements du module :

```powershell
python odoo\odoo-bin -d marketplace_db --addons-path=odoo/addons,odoo/odoo/addons,addons -u marketplace --stop-after-init --db_user=odoo --db_password=CHANGER_MOI
```

### 5.2 Lancement en mode dev

```powershell
python odoo\odoo-bin -d marketplace_db --addons-path=odoo/addons,odoo/odoo/addons,addons --dev=all --db_user=odoo --db_password=CHANGER_MOI
```

Ouvrez ensuite :

- http://localhost:8069

Arrêt : `Ctrl + C`.

---

## 6) Dépannage rapide

### `ModuleNotFoundError: No module named 'odoo'`

- Le submodule n’est pas initialisé : relancez :

```powershell
git submodule update --init --recursive
```

### Erreur PostgreSQL du type `FATAL: role "..." does not exist`

- Créez un rôle PostgreSQL correspondant, ou utilisez `--db_user=odoo --db_password=...` comme dans ce guide.

### `psycopg2` ne s’installe pas

- Vérifiez que vous êtes en **Python 3.11 x64** et que le venv est activé.
- Sinon, installez les **Microsoft C++ Build Tools** (ou utilisez WSL).

---

## 7) (Option) Générer un PDF à partir de ce guide

Le repo fournit ce guide en Markdown. Pour obtenir un PDF :

- Option 1 : VS Code → **Markdown PDF** (extension) → Export PDF.
- Option 2 : `pandoc` (si installé) :

```powershell
pandoc .\GUIDE_WINDOWS.md -o .\GUIDE_WINDOWS.pdf
```

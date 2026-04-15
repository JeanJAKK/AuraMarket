# 🚀 Quick Start - Tests Marketplace

## 5 minutes pour comprendre et exécuter les tests

### 1️⃣ Vérifier que tout est prêt

```bash
cd /home/jakk/Bureau/repository/MarketHub/odoo
ls -la addons/marketplace/tests/
# Doit afficher les fichiers de test
```

### 2️⃣ Lancer tous les tests

```bash
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init
```

**Résultat attendu:**

```
✓ Creating tables...
✓ Loading data...
✓ Running tests...
- test_vendors_page_public ... ok
- test_vendor_profile_public ... ok
- test_product_like_create ... ok
- test_customer_can_follow_vendor ... ok
... (53 tests)

OK - All tests passed (took 30s)
```

### 3️⃣ Si un test échoue

```bash
# Voir les erreurs en détail
python odoo-bin -d marketplace_db -m marketplace --test-enable \
    --stop-after-init --log-level=debug 2>&1 | grep -A10 "ERROR\|FAILED"
```

---

## 🎯 Commandes essentielles

### Lancer un seul fichier de test

```bash
# Tests HTTP seulement
python odoo-bin -d marketplace_db --test-file=addons/marketplace/tests/test_http.py \
    --test-enable --stop-after-init

# Tests d'interactions seulement
python odoo-bin -d marketplace_db --test-file=addons/marketplace/tests/test_interactions.py \
    --test-enable --stop-after-init

# Tests de contrôle d'accès seulement
python odoo-bin -d marketplace_db --test-file=addons/marketplace/tests/test_access_control.py \
    --test-enable --stop-after-init
```

### Lancer une classe de test spécifique

```bash
# HttpCase seulement
python odoo-bin -d marketplace_db --test-tags=MarketplaceHttpCase \
    --test-enable --stop-after-init
```

---

## 📖 Structure minimale pour comprendre

### 3 types de tests

#### 1️⃣ **Tests HTTP** (`test_http.py`)

```python
def test_vendors_page_public(self):
    """Vérifie que /vendors charge et affiche une liste"""
    response = self.url_open('/vendors')
    self.assertEqual(response.status_code, 200)
    self.assertIn(b'Nos vendeurs', response.content)
```

✅ Teste les routes, HTML, redirections

#### 2️⃣ **Tests d'interactions** (`test_interactions.py`)

```python
def test_product_like_create(self):
    """Vérifie qu'un client peut liker un produit"""
    like = self.env['marketplace.product.like'].create({
        'product_id': self.product.id,
        'partner_id': self.customer.id,
    })
    self.assertTrue(like.id)
```

✅ Teste les models, relations, logique métier

#### 3️⃣ **Tests d'accès** (`test_access_control.py`)

```python
def test_public_cannot_like_product(self):
    """Vérifie qu'un visiteur ne peut pas créer de like"""
    # Un visiteur n'a pas de partner_id
    self.assertFalse(self.public_user.partner_id)
```

✅ Teste les permissions, sécurité

---

## 📝 Ajouter rapidement un nouveau test

### Template de base

```python
# Dans le fichier approprié (test_http.py, test_interactions.py ou test_access_control.py)

def test_my_feature(self):
    """Description claire du test"""

    # ARRANGE (préparer)
    data = self._create_test_data()  # ou utiliser les données de setUpClass

    # ACT (exécuter)
    result = data.do_something()

    # ASSERT (vérifier)
    self.assertEqual(result, expected_value)
```

### Exemple complet

```python
def test_vendor_email_is_required(self):
    """Vérifier qu'un vendeur doit avoir un email"""

    # ARRANGE
    # (aucunn setup nécessaire)

    # ACT & ASSERT
    with self.assertRaises(Exception):
        self.env['res.partner'].create({
            'name': 'No Email Vendor',
            'is_vendor': True,
            # 'email': '' # Manquant!
        })
```

### Puis lancer

```bash
# Les tests automatiquement découverts et exécutés
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init
```

---

## 🔧 Helpers utiles (dans conftest.py)

```python
# Accès privé
Like un produit
like = self.env['marketplace.product.like'].create({...})

# Commenter un produit
comment = self.env['marketplace.product.comment'].create({...})

# Suivre un vendeur
vendor.write({'follower_ids': [(4, customer.id)]})

# Chercher des données
products = self.env['product.template'].search([
    ('vendor_id', '=', vendor.id)
])
```

---

## ✅ Assertions courantes

```python
# Existence
self.assertTrue(record.id)  # Enregistrement créé
self.assertFalse(record.exists())  # Supprimé

# Égalité
self.assertEqual(like.product_id, product)
self.assertNotEqual(vendor1.id, vendor2.id)

# Appartenance
self.assertIn(customer, vendor.follower_ids)
self.assertNotIn(customer2, vendor.follower_ids)

# Comparaison
self.assertGreater(count, 0)
self.assertLess(price, 1000)

# Exception
with self.assertRaises(ValidationError):
    bad_data.create()

# HTML (HttpCase)
self.assertIn(b'text', response.content)
```

---

## 📊 Tableau rapide de comparaison

| Besoin             | Classe          | Fichier                | Exemple             |
| ------------------ | --------------- | ---------------------- | ------------------- |
| Tester une route   | HttpCase        | test_http.py           | `/vendors` → 200 OK |
| Tester un model    | TransactionCase | test_interactions.py   | Like creation       |
| Tester permissions | TransactionCase | test_access_control.py | Visiteur vs Client  |

---

## 🐛 Problèmes courants

### ❌ "Database does not exist"

```bash
# Solution: Créer ou réinitialiser la base
cd /home/jakk/Bureau/repository/MarketHub/odoo
python odoo-bin -d marketplace_db -c openerp.conf --init=marketplace
```

### ❌ "ModuleNotFoundError: marketplace"

```bash
# Solution: Vérifier que le module est dans le bon dossier
ls -la addons/marketplace/__manifest__.py  # Doit exister
```

### ❌ "Test takes too long"

```bash
# Utiliser setUpClass au lieu de setUp
@classmethod
def setUpClass(cls):  # ✅ Une fois
    # ...

def setUp(self):  # ❌ Avant chaque test
    # ...
```

### ❌ Test échoue aléatoirement (flaky)

```bash
# Problèmes courants:
# 1. Dépendance entre tests
# 2. Rollback non complet
# 3. Date/heure en dur

# Solution: Isoler complètement chaque test
```

---

## 📞 Aide rapide

| Prob                      | Commande                              |
| ------------------------- | ------------------------------------- |
| Voir les logs             | `tail -f odoo.log`                    |
| Déboguer un test          | Ajouter `import pdb; pdb.set_trace()` |
| Voir quels tests existent | `grep "def test_" test_*.py`          |
| Formatter le code         | `black test_*.py`                     |
| Vérifier la syntaxe       | `python -m py_compile test_*.py`      |

---

## ✨ Checklist avant de committer

- [ ] `python odoo-bin -d marketplace_db -m marketplace --test-enable` pass
- [ ] Aucun test échoue
- [ ] Tests exécutés localement
- [ ] Nouveau code couvert par des tests
- [ ] Noms de tests clairs
- [ ] Pas de print() ou logger en dur

---

**Prêt? Lancez les tests maintenant:**

```bash
cd /home/jakk/Bureau/repository/MarketHub/odoo
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init
```

💚 Tous les tests passent = Code fiable!

# 🎯 CHEATSHEET - Commandes rapides

Mémo des commandes les plus importantes pour les tests.

---

## 🚀 Lancer les tests

### Tous les tests

```bash
cd /home/jakk/Bureau/repository/MarketHub/odoo
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init
```

### Tests spécifiques

```bash
# Tests HTTP seulement
python odoo-bin -d marketplace_db --test-file=addons/marketplace/tests/test_http.py --test-enable --stop-after-init

# Tests d'interactions seulement
python odoo-bin -d marketplace_db --test-file=addons/marketplace/tests/test_interactions.py --test-enable --stop-after-init

# Tests d'accès seulement
python odoo-bin -d marketplace_db --test-file=addons/marketplace/tests/test_access_control.py --test-enable --stop-after-init
```

### Avec le script

```bash
cd addons/marketplace/tests
bash run_tests.sh all          # Tous
bash run_tests.sh http         # HTTP
bash run_tests.sh interactions # Interactions
bash run_tests.sh access       # Accès
```

---

## 🔍 Débogage

### Voir les logs

```bash
tail -f odoo.log
# ou
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init --log-level=debug
```

### Arrêter au premier échec

```bash
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init -x
```

### Voir le traceback complet

```bash
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init --tb=long
```

### Déboguer dans un test

```python
def test_something(self):
    # ...
    import pdb; pdb.set_trace()  # ← Breakpoint
    # ...
```

---

## ✍️ Écrire un test

### Template minimal

```python
def test_my_feature(self):
    """Description claire"""
    # ARRANGE
    data = self.vendor  # ou créer

    # ACT
    result = data.do_something()

    # ASSERT
    self.assertEqual(result, expected)
```

### Assertions courantes

```python
# Existence
self.assertTrue(record.id)
self.assertFalse(record.exists())

# Égalité
self.assertEqual(a, b)
self.assertNotEqual(a, b)

# Appartenance
self.assertIn(item, list)
self.assertNotIn(item, list)

# Comparaison
self.assertGreater(a, b)
self.assertLess(a, b)

# Exception
with self.assertRaises(Exception):
    bad_code()

# Texte
self.assertIn(b'text', response.content)  # bytes!
```

---

## 🛠️ Maintenance

### Ajouter un test

1. Ouvrir le fichier approprié
2. Ajouter une méthode `def test_...`
3. Lancer: `python odoo-bin ... --test-enable --stop-after-init`

### Chercher des tests existants

```bash
grep "def test_" addons/marketplace/tests/test_*.py
grep "def test_" addons/marketplace/tests/test_*.py | wc -l  # Compter
```

### Copier un exemple

```bash
cat addons/marketplace/tests/test_example.py | grep -A15 "def test_product_like"
```

---

## 📚 Documentation rapide

| Besoin           | Fichier           |
| ---------------- | ----------------- |
| Commencer        | QUICKSTART.md     |
| Apprendre        | test_example.py   |
| Bonnes pratiques | BEST_PRACTICES.md |
| Référence        | README.md         |
| Navigation       | INDEX.md          |
| Vue d'ensemble   | SUMMARY.md        |

---

## 🔄 Flux courant

```
1. Modifier code
   ↓
2. Écrire un test pour le nouveau code
   ↓
3. Lancer: python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init
   ↓
4. Tous les tests passent? ✅ Commit!
   ↓
5. Sinon: Déboguer et corriger
```

---

## 💡 Astuces rapides

### Test HTTP (vérifier une URL)

```python
def test_route_loads(self):
    response = self.url_open('/vendors')
    self.assertEqual(response.status_code, 200)
    self.assertIn(b'Vendeurs', response.content)
```

### Test de création

```python
def test_create_record(self):
    record = self.env['model'].create({'name': 'Test'})
    self.assertTrue(record.id)
```

### Test de relation

```python
def test_relation(self):
    self.vendor.write({'follower_ids': [(4, self.customer.id)]})
    self.assertIn(self.customer, self.vendor.follower_ids)
```

### Test d'erreur

```python
def test_validation_error(self):
    with self.assertRaises(Exception):
        self.env['model'].create({'name': ''})  # Erreur
```

---

## 🚨 Problèmes courants

| Problème                            | Solution                                               |
| ----------------------------------- | ------------------------------------------------------ |
| "Database does not exist"           | `python odoo-bin -d marketplace_db --init=marketplace` |
| "Test takes too long"               | Utiliser `setUpClass` au lieu de `setUp`               |
| "Test passed locally, failed in CI" | Dépendance entre tests, utiliser `setUpClass`          |
| "Module not found"                  | Vérifier `addons/marketplace/` existe                  |
| "Assertion failed"                  | Lire l'erreur, vérifier la logique du test             |

---

## 📊 Quick Compare

```python
# ❌ Mauvais
def test_everything(self):
    """Test tout à la fois"""
    like = ...
    comment = ...
    follow = ...
    # Difficile de savoir où ça échoue

# ✅ Bon
def test_like_creates_record(self):
    """Teste UNIQUEMENT la création de like"""
    like = self.env['marketplace.product.like'].create(...)
    self.assertTrue(like.id)

def test_comment_creates_record(self):
    """Teste UNIQUEMENT la création de commentaire"""
    comment = self.env['marketplace.product.comment'].create(...)
    self.assertTrue(comment.id)
```

---

## 🎬 Exécution rapide

```bash
# Tout en une ligne
cd /home/jakk/Bureau/repository/MarketHub/odoo && \
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init

# Avec alias (ajouter dans ~/.bashrc)
alias marketplace-test='cd /home/jakk/Bureau/repository/MarketHub/odoo && python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init'

# Puis utiliser
marketplace-test
```

---

## 📝 Checklist avant commit

- [ ] Tests lancés localement ✅
- [ ] Tous les tests passent
- [ ] Nouveau code a un test
- [ ] Noms de tests clairs
- [ ] Pas de `print()` qui traîne
- [ ] Pas de dépendances entre tests
- [ ] Code formaté (si applicable)

---

**Quick Reference**
Sauvegardez cette page en favori! 🌟

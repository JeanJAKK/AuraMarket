# Bonnes Pratiques pour les Tests Marketplace

## Principes Clés

### 1. **Isolation des tests**

- Chaque test doit être indépendant
- Ne pas faire de dépendances entre tests
- Utiliser `setUpClass` pour initialiser les données communes

```python
@classmethod
def setUpClass(cls):
    super().setUpClass()
    # Créer les données de base utilisées par tous les tests
    cls.vendor = cls.env['res.partner'].create({...})
```

### 2. **Nommage clair**

- Commencer par `test_`
- Décriver ce qu'on teste dans le nom
- ✅ Bon: `test_vendor_can_add_product`
- ❌ Mauvais: `test_vendor`

### 3. **Une assertion par test** (princip SINGLE RESPONSIBILITY)

- Chaque test = UNE fonctionnalité
- Facilite le debugging

```python
# ✅ Bon - Tests séparés
def test_like_creates_record(self):
    like = self.env['marketplace.product.like'].create({...})
    self.assertTrue(like.id)

def test_like_has_correct_product(self):
    like = self.env['marketplace.product.like'].create({...})
    self.assertEqual(like.product_id, self.product)
```

### 4. **Setup/Teardown**

```python
def setUp(self):
    """Appelé avant chaque test (TransactionCase rollback)"""
    super().setUp()
    # Données spécifiques au test

def tearDown(self):
    """Appelé après chaque test"""
    # Cleanup si nécessaire
    super().tearDown()
```

## Types de Tests

### Tests HttpCase (tests HTTP en ligne)

```python
from odoo.tests.common import HttpCase

class MyHttpTest(HttpCase):
    def test_page_loads(self):
        # Naviguer vers une URL
        response = self.url_open('/vendors', timeout=10)
        self.assertEqual(response.status_code, 200)
        # Vérifier le contenu
        self.assertIn(b'Vendeurs', response.content)
```

### Tests TransactionCase (tests unitaires)

```python
from odoo.tests.common import TransactionCase

class MyTransactionTest(TransactionCase):
    def test_like_product(self):
        # Créer les données
        like = self.env['marketplace.product.like'].create({
            'product_id': self.product.id,
            'partner_id': self.customer.id,
        })
        # Vérifier
        self.assertTrue(like.id)
        # Rollback automatique après le test
```

## Assertions Utiles

### Existence et ID

```python
self.assertTrue(record.id)  # Enregistrement créé
self.assertFalse(record.exists())  # Enregistrement supprimé
```

### Égalité

```python
self.assertEqual(like.product_id, self.product)
self.assertNotEqual(vendor1.id, vendor2.id)
```

### Appartenance

```python
self.assertIn(self.customer, self.vendor.follower_ids)
self.assertNotIn(self.customer2, self.vendor.follower_ids)
```

### Comparaisons

```python
self.assertGreater(likes_count, 0)
self.assertGreaterEqual(len(followers), 3)
self.assertLess(products_count, 100)
```

### Exceptions

```python
with self.assertRaises(ValidationError):
    self.env['marketplace.product.comment'].create({
        'product_id': self.product.id,
        'partner_id': self.customer.id,
        'content': '',  # Vide = erreur
    })
```

### Contenu HTML (HttpCase)

```python
response = self.url_open('/vendors')
self.assertIn(b'Test Shop', response.content)  # bytes!
```

## Pattern: Arrange-Act-Assert (AAA)

Tous les tests doivent suivre ce pattern:

```python
def test_vendor_follow(self):
    # ARRANGE: Préparer les données
    vendor = self.env['res.partner'].create({
        'name': 'Test Vendor',
        'is_vendor': True,
    })
    customer = self.env['res.partner'].create({
        'name': 'Test Customer',
    })

    # ACT: Exécuter l'action
    vendor.write({'follower_ids': [(4, customer.id)]})

    # ASSERT: Vérifier le résultat
    self.assertIn(customer, vendor.follower_ids)
```

## Helpers pour Réduire la Duplication

Dans `conftest.py`, créer des helpers:

```python
def _like_product(self, product, customer):
    """Helper pour liker un produit"""
    return self.env['marketplace.product.like'].create({
        'product_id': product.id,
        'partner_id': customer.id,
    })

# Utilisation dans les tests
def test_like_count(self):
    self._like_product(self.product, self.customer1)
    self._like_product(self.product, self.customer2)
    # ...
```

## Checklist de Test

Avant de committer du code:

- [ ] Tous les tests passent: `./run_tests.sh all`
- [ ] Nouveaux tests écrits pour la nouvelle fonctionnalité
- [ ] Au moins un test pour le cas normal
- [ ] Au moins un test pour le cas d'erreur
- [ ] Tests d'accès (public/client/vendeur)
- [ ] Pas de dépendances entre tests
- [ ] Noms de tests clairs et descriptifs
- [ ] Aucun `print()` ou `logger.info()` pour déboguer
- [ ] Pas de données en dur (utiliser setUpClass)

## Couverture de Code

### Vérifier la couverture

```bash
cd /home/jakk/Bureau/repository/MarketHub/odoo
python odoo-bin -d marketplace_db -m marketplace --test-enable \
    --log-level=debug --stop-after-init 2>&1 | grep -i "cover"
```

### Objectif minimum: 80% de couverture

- 100% für les models critiques
- 80% pour les vues et contrôleurs
- 70% pour les helpers

## Cas Particuliers

### Test avec fichier (upload image)

```python
from io import BytesIO

def test_product_with_image(self):
    image_data = BytesIO(b'fake image')
    # Simuler l'upload
    product = self.env['product.template'].create({
        'name': 'Product',
        'image_1920': base64.b64encode(image_data.getvalue()).decode('utf-8'),
    })
    self.assertEqual(product.image_1920, ...)
```

### Test d'accès/permissions

```python
def test_vendor_cannot_see_other_vendor_product(self):
    # Vendor 1 essaie de voir le produit de Vendor 2
    product = self.env['product.template'].sudo(self.vendor1_user).search([
        ('vendor_id', '=', self.vendor2.id)
    ])
    # Dépend des ACL configurées
```

### Test avec utilisateur connecté

```python
def test_customer_like_as_user(self):
    # Utiliser sudo(user) pour simuler l'utilisateur connecté
    like = self.env['marketplace.product.like'].sudo(self.customer_user).create({
        'product_id': self.product.id,
        'partner_id': self.customer.id,
    })
    self.assertTrue(like.id)
```

## Debugging de Tests

### Afficher les erreurs en détail

```bash
python odoo-bin -d marketplace_db -m marketplace --test-enable \
    --log-level=debug --stop-after-init --tb=short
```

### Lancer un test spécifique

```bash
python odoo-bin -d marketplace_db --test-file=/path/to/test_file.py \
    --test-enable --stop-after-init
```

### Utiliser pdb pour déboguer

```python
def test_something(self):
    # ...
    import pdb; pdb.set_trace()  # Breakpoint
    # ...
```

## Ressources

- [Odoo Testing Documentation](https://www.odoo.com/documentation/17.0/developer/misc/other/testing.html)
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [AssertionError Reference](https://docs.python.org/3/library/unittest.html#test-cases)

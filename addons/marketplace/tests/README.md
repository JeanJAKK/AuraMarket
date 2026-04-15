# Tests du Module Marketplace

Cet ensemble de tests garantit la fiabilité et la cohérence des fonctionnalités du marketplace.

## Structure des tests

### 1. **Tests HTTP (test_http.py)**

Vérifient que toutes les URLs répondent correctement:

- ✅ `/vendors` - Liste des vendeurs (public)
- ✅ `/vendors/<id>` - Profil vendeur (public)
- ✅ `/vendors/search` - Recherche (public)
- ✅ `/marketplace` - Accueil marketplace (public)
- ✅ `/my/vendor/dashboard` - Dashboard vendeur (authentifié)
- ✅ `/my/vendor/product/new` - Formulaire ajout produit (authentifié)
- ✅ Vérification des 404 pour URLs invalides
- ✅ Vérification des redirections de login

### 2. **Tests d'interactions (test_interactions.py)**

Testent les fonctionnalités métier:

- ✅ **Like produit** - Création, pas de doublons, comptage
- ✅ **Follow vendeur** - Ajouter/retirer un follower
- ✅ **Commentaires** - Créer, vérifier le contenu obligatoire, comptage
- ✅ **Ajout produit** - Création, avec/sans image
- ✅ **Relations** - Produit-vendeur, statistiques

### 3. **Tests de contrôle d'accès (test_access_control.py)**

Vérifient les permissions par rôle:

- ✅ **Visiteur (public)** - Peut voir vendeurs/produits, ne peut pas liker
- ✅ **Client** - Peut liker, commenter, suivre des vendeurs
- ✅ **Vendeur** - Peut gérer ses produits, voir son dashboard
- ✅ **Isolation** - Vendeur ne voit que ses propres produits

## Comment lancer les tests

### Lancer tous les tests du module

```bash
cd /home/jakk/Bureau/repository/MarketHub/odoo
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init
```

### Lancer un fichier de test spécifique

```bash
python odoo-bin -d marketplace_db -m marketplace.tests.test_http --test-enable --stop-after-init
python odoo-bin -d marketplace_db -m marketplace.tests.test_interactions --test-enable --stop-after-init
python odoo-bin -d marketplace_db -m marketplace.tests.test_access_control --test-enable --stop-after-init
```

### Lancer une classe de test spécifique

```bash
python odoo-bin -d marketplace_db --test-tags=marketplace.MarketplaceHttpCase --stop-after-init
```

### Avec la sortie détaillée

```bash
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init --log-level=debug
```

## Cas de test couverts

### Scénario 1: Achat et interactions client

1. Client visite un vendeur
2. Client devient follower du vendeur
3. Client like un produit
4. Client commente un produit
5. Stats du vendeur sont à jour

### Scénario 2: Gestion produit vendeur

1. Vendeur crée un produit avec image
2. Produit apparaît sur le marketplace
3. Clients peuvent voir et interagir
4. Vendeur voit les stats dans le dashboard

### Scénario 3: Recherche et découverte

1. Visiteur recherche un produit
2. Résultats filtrés par nom et vendeur
3. Images s'affichent correctement
4. Navigation vers profil vendeur fonctionne

## Résultats attendus

Tous les tests doivent passer:

```
✓ test_vendors_page_public
✓ test_vendor_profile_public
✓ test_product_like_create
✓ test_customer_can_follow_vendor
✓ test_public_can_view_vendors
✓ test_vendor_can_add_product
... (30+ tests)

Ran XX tests in XXs
OK - All tests passed
```

## Troubleshooting

Si un test échoue:

1. Vérifier les logs: `tail -f odoo.log | grep -i error`
2. Vérifier que la base de données est à jour: `./odoo-bin -d marketplace_db --update=marketplace`
3. Vérifier les fichiers modifiés récemment avec `git status`
4. Lancer le test individuellement avec `--log-level=debug`

## Maintenance

- Ajouter des tests pour chaque nouvelle fonctionnalité
- Exécuter les tests avant chaque commit
- Maintenir une couverture de test > 80%

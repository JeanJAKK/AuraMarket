# 📚 INDEX - Navigation dans les Tests

Bienvenue dans la suite de tests du Marketplace! Voici comment naviguer.

---

## 🗂️ Arborescence des fichiers

```
tests/
├── 📌 INDEX.md (vous êtes ici)
├── 🚀 QUICKSTART.md              ← Commencez par là (5 min)
├── 📖 README.md                   ← Documentation complète
├── 💡 BEST_PRACTICES.md           ← Comment bien tester
├── 📋 SUMMARY.md                  ← Aperçu des 53+ tests
├── 👨‍💻 test_example.py              ← 28 exemples annotés
│
├── 🌐 test_http.py                ← Tests des routes HTTP
├── 💬 test_interactions.py        ← Tests des actions (like, follow, etc.)
├── 🔐 test_access_control.py     ← Tests des permissions
│
├── 🔧 conftest.py                 ← Fixtures et helpers
└── 🎬 run_tests.sh                ← Script pour lancer les tests
```

---

## 🎯 Par où commencer?

### 1️⃣ **Je veux exécuter les tests rapidement**

→ Allez à [`QUICKSTART.md`](./QUICKSTART.md) (5 minutes)

```bash
python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init
```

### 2️⃣ **Je veux comprendre comment les tests fonctionnent**

→ Allez à [`test_example.py`](./test_example.py) (28 exemples annotés)

Montre comment:

- Créer des données de test
- Écrire des assertions
- Utiliser le pattern AAA
- Tester HTTP et models

### 3️⃣ **Je veux apprendre les bonnes pratiques**

→ Allez à [`BEST_PRACTICES.md`](./BEST_PRACTICES.md)

Couvre:

- Nommage des tests
- Structure des tests
- Assertions courantes
- Debugging
- Patterns à utiliser

### 4️⃣ **Je veux ajouter un nouveau test**

→ Lire [`test_example.py`](./test_example.py) + [`BEST_PRACTICES.md`](./BEST_PRACTICES.md)

Puis modifier le fichier approprié:

- Routes HTTP? → [`test_http.py`](./test_http.py)
- Logique métier? → [`test_interactions.py`](./test_interactions.py)
- Permissions? → [`test_access_control.py`](./test_access_control.py)

### 5️⃣ **Je veux une vue d'ensemble**

→ Allez à [`SUMMARY.md`](./SUMMARY.md)

Montre:

- Tous les 53+ tests
- Types de tests
- Étendue de la couverture
- Statistiques

### 6️⃣ **Je veux la documentation complète**

→ Allez à [`README.md`](./README.md)

Couvre:

- Guide d'exécution détaillé
- Cas de test couverts
- Troubleshooting
- Maintenance

---

## 📊 Aperçu des fichiers de test

### 🌐 [`test_http.py`](./test_http.py) - Tests des routes

**Qu'est-ce que c'est:** Vérifie que les URLs répondent correctement
**Classe:** `MarketplaceHttpCase`
**Nombre de tests:** 10
**Temps:** ~5-10 secondes

**Teste:**

- ✅ `/vendors` - Liste des vendeurs
- ✅ `/vendors/<id>` - Profil vendeur
- ✅ `/vendors/search` - Recherche
- ✅ `/marketplace` - Accueil
- ✅ Routes authentifiées (redirections)

**À utiliser quand:**

- Ajouter une nouvelle route
- Modifier le template d'une page
- Tester le rendu HTML

---

### 💬 [`test_interactions.py`](./test_interactions.py) - Tests des interactions

**Qu'est-ce que c'est:** Vérifie la logique métier (like, follow, commentaires)
**Classe:** `ProductInteractionCase`
**Nombre de tests:** 12
**Temps:** ~15 secondes

**Teste:**

- ✅ Like: création, contrainte unique, comptage
- ✅ Follow: ajouter/retirer followers
- ✅ Commentaires: création, validation
- ✅ Produits: création, relations, stats

**À utiliser quand:**

- Modifier la logique d'un model
- Ajouter une contrainte
- Tester une interaction utilisateur

---

### 🔐 [`test_access_control.py`](./test_access_control.py) - Tests d'accès

**Qu'est-ce que c'est:** Vérifie les permissions (visiteur/client/vendeur)
**Classe:** `AccessControlCase`
**Nombre de tests:** 13
**Temps:** ~20 secondes

**Teste:**

- ✅ Visiteur: peut voir, ne peut pas liker
- ✅ Client: peut liker, commenter, suivre
- ✅ Vendeur: peut gérer ses produits
- ✅ Isolation: vendeur ne voit que ses données

**À utiliser quand:**

- Ajouter un contrôle d'accès
- Modifier les permissions
- Vérifier la sécurité après refacto

---

### 👨‍💻 [`test_example.py`](./test_example.py) - Exemples complets

**Qu'est-ce que c'est:** Template avec 28 exemples annotés
**Classe:** `ExampleTestsTemplate + ExampleHttpTest`
**Nombre de tests:** 18
**Temps:** ~10 secondes

**Montre:**

- ✅ Comment structurer un test
- ✅ Pattern AAA
- ✅ Helpers et fixtures
- ✅ Assertions courantes
- ✅ Tests HTTP vs Models

**À utiliser quand:**

- Apprendre à écrire des tests
- Besoin d'un template
- Chercher comment faire quelque chose

---

## 🔧 Fichiers utilitaires

### [`conftest.py`](./conftest.py)

Classes de base réutilisables:

```python
# Classe de base avec données pré-créées
class MarketplaceTestBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        # Crée 2 vendeurs, 3 clients, produits
        # Utile pour éviter duplication
```

Helpers:

```python
self._like_product(product, customer)
self._comment_product(product, customer, content)
self._follow_vendor(vendor, customer)
```

---

## 🎬 Scripts et commandes

### [`run_tests.sh`](./run_tests.sh)

Script shell pour lancer les tests facilement:

```bash
bash run_tests.sh all          # Tous les tests
bash run_tests.sh http         # Tests HTTP seulement
bash run_tests.sh interactions # Tests d'interactions
bash run_tests.sh access       # Tests d'accès
```

---

## 🌳 Arbre de décision

```
Vous devez tester quoi?
│
├─ Une route HTTP (URL, rendu)?
│  └─→ test_http.py (HttpCase)
│
├─ Un model ou une interaction?
│  └─→ test_interactions.py (TransactionCase)
│
├─ Les permissions/accès?
│  └─→ test_access_control.py (TransactionCase)
│
├─ Vous apprenez à tester?
│  └─→ test_example.py (28 exemples)
│
└─ Vous ne savez pas par où commencer?
   └─→ QUICKSTART.md (5 minutes)
```

---

## 📚 Guide de lecture recommandé

### Pour les débutants:

1. [`QUICKSTART.md`](./QUICKSTART.md) - 5 min
2. [`test_example.py`](./test_example.py) - 15 min
3. Essayer les commandes - 5 min
4. Écrire votre premier test - 10 min

**Total: 35 minutes**

### Pour les intermédiaires:

1. [`test_example.py`](./test_example.py) - 5 min
2. [`BEST_PRACTICES.md`](./BEST_PRACTICES.md) - 15 min
3. Consulter [`test_*.py`](.) selon besoins

### Pour avancés:

1. Consulter directement [`test_*.py`](.)
2. Utiliser [`conftest.py`](./conftest.py) comme base
3. Ajouter des tests héités de ces classes

---

## ✅ Checklist de premiers pas

- [ ] Lire [`QUICKSTART.md`](./QUICKSTART.md) (5 min)
- [ ] Lancer les tests: `python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init`
- [ ] Vérifier qu'ils passent tous ✅
- [ ] Lire un test dans [`test_example.py`](./test_example.py)
- [ ] Comprendre le pattern AAA
- [ ] Ajouter un petit test
- [ ] Être fier 🎉

---

## 🔗 Liens rapides

| Besoin                      | Fichier                                              |
| --------------------------- | ---------------------------------------------------- |
| **Comment lancer?**         | [`QUICKSTART.md`](./QUICKSTART.md)                   |
| **Documentation complète?** | [`README.md`](./README.md)                           |
| **Bonnes pratiques?**       | [`BEST_PRACTICES.md`](./BEST_PRACTICES.md)           |
| **Exemples?**               | [`test_example.py`](./test_example.py)               |
| **Statistiques?**           | [`SUMMARY.md`](./SUMMARY.md)                         |
| **Routes HTTP?**            | [`test_http.py`](./test_http.py)                     |
| **Logique métier?**         | [`test_interactions.py`](./test_interactions.py)     |
| **Permissions?**            | [`test_access_control.py`](./test_access_control.py) |
| **Helpers?**                | [`conftest.py`](./conftest.py)                       |
| **Script?**                 | [`run_tests.sh`](./run_tests.sh)                     |

---

## 💡 Conseils rapides

1. **Tous les tests échouent?**
   - Vérifier que la base existe: `ls /var/lib/odoo/marketplace_db.db`
   - Si besoin, réinitialiser: `python odoo-bin -d marketplace_db --init=marketplace`

2. **Un test échoue?**
   - Lire le message d'erreur
   - Voir [`BEST_PRACTICES.md`](./BEST_PRACTICES.md) section "Debugging"

3. **Vous ne savez pas comment tester quelque chose?**
   - S'inspirer d'un test similaire dans [`test_example.py`](./test_example.py)
   - Consulter [`BEST_PRACTICES.md`](./BEST_PRACTICES.md)

4. **Ajouter rapidement un test?**
   - Copier un exemple de [`test_example.py`](./test_example.py)
   - L'adapter à votre besoin
   - Lancer: `python odoo-bin -d marketplace_db -m marketplace --test-enable --stop-after-init`

---

**Status**: ✅ Suite de tests complète, bien documentée, prête à l'emploi
**Nombre de tests**: 53+
**Couverture**: ~80%
**Documentation**: 6 fichiers (README, QUICKSTART, BEST_PRACTICES, SUMMARY, INDEX, test_example)

**Commencez maintenant!** 🚀

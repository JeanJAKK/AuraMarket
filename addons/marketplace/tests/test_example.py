# -*- coding: utf-8 -*-
"""
EXEMPLE DE TEST - Template à copier et adapter

Ce fichier montre comment écrire des tests de qualité pour le marketplace.
Utilisez-le comme modèle pour ajouter de nouveaux tests.
"""

from odoo.tests.common import TransactionCase, HttpCase
from odoo.exceptions import ValidationError, AccessError


class ExampleTestsTemplate(TransactionCase):
    """
    Exemple d'une suite de tests complète.
    
    Structure:
    1. setUpClass - Données communes à tous les tests
    2. test_* méthodes - Les tests réels
    3. Helpers - Méthodes utilitaires
    """

    @classmethod
    def setUpClass(cls):
        """
        setUp classe - exécuté UNE FOIS avant tous les tests
        
        Crée les données de base (vendeur, produit, utilisateur).
        Ces données sont partagées entre tous les tests.
        Chaque test rollback automatiquement après lui.
        """
        super(ExampleTestsTemplate, cls).setUpClass()
        
        # 1. Créer un vendeur de test
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Example Vendor',
            'shop_name': 'Example Shop',
            'is_vendor': True,
            'supplier_rank': 1,
            'email': 'example@vendor.com',
        })
        
        # 2. Créer un client de test
        cls.customer = cls.env['res.partner'].create({
            'name': 'Example Customer',
            'email': 'example@customer.com',
        })
        
        # 3. Créer un produit de test
        cls.product = cls.env['product.template'].create({
            'name': 'Example Product',
            'list_price': 99.99,
            'vendor_id': cls.vendor.id,
            'description_sale': 'This is an example product',
        })

    def test_01_product_creation(self):
        """
        TEST 1: Vérifier qu'un produit peut être créé
        
        Pattern AAA:
        - Arrange: Les données sont déjà dans setUpClass
        - Act: On crée un nouveau produit
        - Assert: On vérifie que le produit existe
        """
        # ARRANGE
        vendor = self.vendor
        
        # ACT
        new_product = self.env['product.template'].create({
            'name': 'New Example Product',
            'list_price': 50.00,
            'vendor_id': vendor.id,
        })
        
        # ASSERT
        self.assertTrue(new_product.id, "Le produit doit avoir un ID")
        self.assertEqual(new_product.name, 'New Example Product')
        self.assertEqual(new_product.list_price, 50.00)
        self.assertEqual(new_product.vendor_id, vendor)

    def test_02_product_like(self):
        """
        TEST 2: Vérifier qu'un client peut liker un produit
        
        Points clés:
        - Tester la création de like
        - Vérifier la relation produit-client
        - Vérifier la contrainte unique (pas de double like)
        """
        # ARRANGE
        product = self.product
        customer = self.customer
        
        # ACT
        like = self.env['marketplace.product.like'].create({
            'product_id': product.id,
            'partner_id': customer.id,
        })
        
        # ASSERT
        self.assertTrue(like.id)
        self.assertEqual(like.product_id, product)
        self.assertEqual(like.partner_id, customer)

    def test_03_product_like_unique_constraint(self):
        """
        TEST 3: Vérifier la contrainte unique pour les likes
        
        Un même utilisateur ne peut liker qu'une fois par produit.
        """
        # ARRANGE
        product = self.product
        customer = self.customer
        
        # ACT: Créer un premier like
        like1 = self.env['marketplace.product.like'].create({
            'product_id': product.id,
            'partner_id': customer.id,
        })
        
        # ASSERT: Vérifier qu'il existe qu'UNE fois
        likes = self.env['marketplace.product.like'].search([
            ('product_id', '=', product.id),
            ('partner_id', '=', customer.id),
        ])
        
        # La contrainte unique doit empêcher le double
        self.assertEqual(len(likes), 1, "Un seul like par utilisateur")

    def test_04_like_count(self):
        """
        TEST 4: Compter les likes d'un produit
        
        Teste la logique de comptage que le dashboard utilise.
        """
        # ARRANGE: Créer 3 clients différents
        customers = []
        for i in range(3):
            customer = self.env['res.partner'].create({
                'name': f'Customer {i}',
                'email': f'customer{i}@test.com',
            })
            customers.append(customer)
        
        # ACT: Liker le produit avec chaque client
        for customer in customers:
            self.env['marketplace.product.like'].create({
                'product_id': self.product.id,
                'partner_id': customer.id,
            })
        
        # ASSERT: Vérifier le comptage
        like_count = self.env['marketplace.product.like'].search_count([
            ('product_id', '=', self.product.id)
        ])
        self.assertEqual(like_count, 3, "Doit avoir 3 likes")

    def test_05_comment_creation(self):
        """
        TEST 5: Vérifier qu'un client peut commenter un produit
        """
        # ARRANGE
        product = self.product
        customer = self.customer
        comment_text = "This is a great product!"
        
        # ACT
        comment = self.env['marketplace.product.comment'].create({
            'product_id': product.id,
            'partner_id': customer.id,
            'content': comment_text,
        })
        
        # ASSERT
        self.assertTrue(comment.id)
        self.assertEqual(comment.product_id, product)
        self.assertEqual(comment.partner_id, customer)
        self.assertEqual(comment.content, comment_text)

    def test_06_comment_empty_content_fails(self):
        """
        TEST 6: Vérifier qu'un commentaire vide est rejeté
        
        Teste le cas d'erreur / validation.
        """
        # ARRANGE
        product = self.product
        customer = self.customer
        
        # ASSERT: Vérifier que la création échoue
        with self.assertRaises(Exception):  # Peut être ValidationError
            self.env['marketplace.product.comment'].create({
                'product_id': product.id,
                'partner_id': customer.id,
                'content': '',  # Vide = erreur
            })

    def test_07_vendor_follow(self):
        """
        TEST 7: Vérifier qu'un client peut suivre un vendeur
        """
        # ARRANGE
        vendor = self.vendor
        customer = self.customer
        
        # ACT: Ajouter le client aux followers
        vendor.write({
            'follower_ids': [(4, customer.id)]
        })
        
        # ASSERT
        self.assertIn(customer, vendor.follower_ids)

    def test_08_vendor_unfollow(self):
        """
        TEST 8: Vérifier qu'un client peut se désabonner
        """
        # ARRANGE
        vendor = self.vendor
        customer = self.customer
        
        # ACT 1: Suivre d'abord
        vendor.write({
            'follower_ids': [(4, customer.id)]
        })
        self.assertIn(customer, vendor.follower_ids)
        
        # ACT 2: Se désabonner
        vendor.write({
            'follower_ids': [(3, customer.id)]
        })
        
        # ASSERT
        self.assertNotIn(customer, vendor.follower_ids)

    def test_09_product_vendor_relation(self):
        """
        TEST 9: Vérifier la relation produit-vendeur
        
        Tests de relation many2one.
        """
        # ARRANGE
        vendor = self.vendor
        
        # ACT: Chercher tous les produits du vendeur
        products = self.env['product.template'].search([
            ('vendor_id', '=', vendor.id)
        ])
        
        # ASSERT
        self.assertGreater(len(products), 0, "Vendeur doit avoir au moins 1 produit")
        self.assertIn(self.product, products)

    def test_10_vendor_statistics(self):
        """
        TEST 10: Vérifier le calcul des statistiques d'un vendeur
        
        Teste la logique que le dashboard utilise.
        """
        # ARRANGE: Créer likes et commentaires
        for i in range(2):
            customer = self.env['res.partner'].create({
                'name': f'Stat Customer {i}',
            })
            self.env['marketplace.product.like'].create({
                'product_id': self.product.id,
                'partner_id': customer.id,
            })
            self.env['marketplace.product.comment'].create({
                'product_id': self.product.id,
                'partner_id': customer.id,
                'content': f'Comment {i}',
            })
        
        # ACT: Calculer les stats
        total_likes = self.env['marketplace.product.like'].search_count([
            ('product_id.vendor_id', '=', self.vendor.id)
        ])
        total_comments = self.env['marketplace.product.comment'].search_count([
            ('product_id.vendor_id', '=', self.vendor.id)
        ])
        
        # ASSERT
        self.assertEqual(total_likes, 2)
        self.assertEqual(total_comments, 2)

    # ===== HELPERS =====
    # Créer des fonctions réutilisables pour simplifier les tests
    
    def _create_test_customer(self, name="Test Customer", email="test@customer.com"):
        """Créer un client de test rapidement"""
        return self.env['res.partner'].create({
            'name': name,
            'email': email,
        })
    
    def _like_product(self, product, customer):
        """Helper pour liker un produit en une ligne"""
        return self.env['marketplace.product.like'].create({
            'product_id': product.id,
            'partner_id': customer.id,
        })
    
    def _comment_product(self, product, customer, content):
        """Helper pour commenter un produit"""
        return self.env['marketplace.product.comment'].create({
            'product_id': product.id,
            'partner_id': customer.id,
            'content': content,
        })


class ExampleHttpTest(HttpCase):
    """
    Exemple d'un test HTTP.
    
    Plus lent que TransactionCase, à utiliser pour:
    - Vérifier que les routes répondent
    - Tester le rendu HTML
    - Vérifier les redirections
    """
    
    @classmethod
    def setUpClass(cls):
        super(ExampleHttpTest, cls).setUpClass()
        
        # Créer un vendeur avec un produit
        cls.vendor = cls.env['res.partner'].create({
            'name': 'HTTP Vendor',
            'is_vendor': True,
            'supplier_rank': 1,
        })
        
        cls.product = cls.env['product.template'].create({
            'name': 'HTTP Product',
            'list_price': 99.99,
            'vendor_id': cls.vendor.id,
        })
    
    def test_vendors_page_loads(self):
        """Tester que la page /vendors charge"""
        # Naviguer vers l'URL
        response = self.url_open('/vendors', timeout=10)
        
        # Vérifier le code HTTP
        self.assertEqual(response.status_code, 200)
        
        # Vérifier le contenu (attention: bytes!)
        self.assertIn(b'Nos vendeurs', response.content)
        self.assertIn(b'HTTP Vendor', response.content)
    
    def test_vendor_profile_loads(self):
        """Tester que le profil vendeur charge"""
        response = self.url_open(f'/vendors/{self.vendor.id}', timeout=10)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'HTTP Vendor', response.content)
    
    def test_invalid_vendor_returns_404(self):
        """Tester qu'un vendeur invalide retourne 404"""
        response = self.url_open('/vendors/999999', timeout=10)
        
        self.assertEqual(response.status_code, 404)

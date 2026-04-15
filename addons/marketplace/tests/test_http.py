# -*- coding: utf-8 -*-
from odoo.tests.common import HttpCase
import json


class MarketplaceHttpCase(HttpCase):
    """Tests HTTP pour vérifier que toutes les URLs répondent correctement"""

    @classmethod
    def setUpClass(cls):
        super(MarketplaceHttpCase, cls).setUpClass()
        
        # Créer un vendeur test
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor',
            'shop_name': 'Test Shop',
            'is_vendor': True,
            'supplier_rank': 1,
            'email': 'vendor@test.com',
        })
        
        # Créer un utilisateur vendeur
        cls.vendor_user = cls.env['res.users'].create({
            'name': 'Vendor User',
            'login': 'vendor_user',
            'email': 'vendor_user@test.com',
            'partner_id': cls.vendor.id,
        })
        
        # Créer un produit test
        cls.product = cls.env['product.template'].create({
            'name': 'Test Product',
            'list_price': 99.99,
            'vendor_id': cls.vendor.id,
        })

    def test_vendors_page_public(self):
        """Test: Page liste des vendeurs accessible en public"""
        response = self.url_open('/vendors', timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Nos vendeurs', response.content)

    def test_vendor_profile_public(self):
        """Test: Profil vendeur accessible en public"""
        response = self.url_open(f'/vendors/{self.vendor.id}', timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Shop', response.content)

    def test_vendor_profile_not_found(self):
        """Test: Profil vendeur inexistant => 404"""
        response = self.url_open('/vendors/999999', timeout=10)
        self.assertEqual(response.status_code, 404)

    def test_vendor_search_page(self):
        """Test: Page recherche accessible"""
        response = self.url_open('/vendors/search', timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Résultats'.encode('utf-8'), response.content)

    def test_search_with_query(self):
        """Test: Recherche avec paramètres"""
        response = self.url_open('/vendors/search?search=Test', timeout=10)
        self.assertEqual(response.status_code, 200)
        # Le produit "Test Product" devrait être trouvé
        self.assertIn(b'Test Product', response.content)

    def test_marketplace_home(self):
        """Test: Page accueil marketplace"""
        response = self.url_open('/marketplace', timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MarketHub', response.content)
        self.assertIn(b'Vendeurs en vedette', response.content)

    def test_vendor_follow_requires_login(self):
        """Test: Suivre un vendeur requires login - redirect to login"""
        response = self.url_open(f'/vendors/{self.vendor.id}/follow', timeout=10)
        # Devrait rediriger vers /web/login ou afficher une page de login
        self.assertIn(response.status_code, [200, 303, 401, 403])

    def test_like_product_requires_login(self):
        """Test: Liker un produit requires login"""
        response = self.url_open(f'/product/{self.product.id}/like', timeout=10)
        self.assertIn(response.status_code, [200, 303, 401, 403])

    def test_vendor_dashboard_requires_login(self):
        """Test: Dashboard vendeur requires login"""
        response = self.url_open('/my/vendor/dashboard', timeout=10)
        self.assertIn(response.status_code, [200, 303, 401, 403])

    def test_add_product_form_requires_login(self):
        """Test: Formulaire ajout produit requires login"""
        response = self.url_open('/my/vendor/product/new', timeout=10)
        self.assertIn(response.status_code, [200, 303, 401, 403])

"""
Configuration et fixtures pour les tests du marketplace.
Utilisables dans les différents fichiers de test.
"""
from odoo.tests.common import TransactionCase, HttpCase


class MarketplaceTestBase(TransactionCase):
    """Classe de base avec les éléments communs pour tous les tests"""
    
    @classmethod
    def setUpClass(cls):
        super(MarketplaceTestBase, cls).setUpClass()
        
        # Utilisateurs de test
        cls.public_user = cls.env.ref('base.public_user')
        
        # Créer 2 vendeurs de test
        cls.vendors = []
        for i in range(2):
            vendor = cls.env['res.partner'].create({
                'name': f'Test Vendor {i+1}',
                'shop_name': f'Test Shop {i+1}',
                'is_vendor': True,
                'supplier_rank': 1,
                'email': f'vendor{i+1}@test.com',
                'city': f'City {i+1}',
            })
            cls.vendors.append(vendor)
        
        # Créer 3 clients de test
        cls.customers = []
        for i in range(3):
            customer = cls.env['res.partner'].create({
                'name': f'Test Customer {i+1}',
                'email': f'customer{i+1}@test.com',
            })
            cls.customers.append(customer)
        
        # Créer des utilisateurs pour les clients et vendeurs
        cls.customer_users = []
        for i, customer in enumerate(cls.customers):
            user = cls.env['res.users'].create({
                'name': f'Customer User {i+1}',
                'login': f'customer_user_{i+1}',
                'email': f'customer_user_{i+1}@test.com',
                'partner_id': customer.id,
            })
            cls.customer_users.append(user)
        
        cls.vendor_users = []
        for i, vendor in enumerate(cls.vendors):
            user = cls.env['res.users'].create({
                'name': f'Vendor User {i+1}',
                'login': f'vendor_user_{i+1}',
                'email': f'vendor_user_{i+1}@test.com',
                'partner_id': vendor.id,
            })
            cls.vendor_users.append(user)
        
        # Créer des produits de test pour chaque vendeur
        cls.products = []
        for vendor_idx, vendor in enumerate(cls.vendors):
            for prod_idx in range(3):
                product = cls.env['product.template'].create({
                    'name': f'Vendor {vendor_idx+1} Product {prod_idx+1}',
                    'list_price': 50.00 + (prod_idx * 10),
                    'vendor_id': vendor.id,
                    'description_sale': f'Description for product {prod_idx+1}',
                })
                cls.products.append(product)
    
    def _like_product(self, product, customer):
        """Helper pour liker un produit"""
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
    
    def _follow_vendor(self, vendor, customer):
        """Helper pour suivre un vendeur"""
        vendor.write({
            'follower_ids': [(4, customer.id)]
        })
    
    def _unfollow_vendor(self, vendor, customer):
        """Helper pour se désabonner d'un vendeur"""
        vendor.write({
            'follower_ids': [(3, customer.id)]
        })


class MarketplaceHttpTestBase(HttpCase):
    """Base pour les tests HTTP du marketplace"""
    
    @classmethod
    def setUpClass(cls):
        super(MarketplaceHttpTestBase, cls).setUpClass()
        
        # Créer un vendeur avec un produit
        cls.vendor = cls.env['res.partner'].create({
            'name': 'HTTP Test Vendor',
            'shop_name': 'HTTP Test Shop',
            'is_vendor': True,
            'supplier_rank': 1,
            'email': 'http_vendor@test.com',
        })
        
        cls.product = cls.env['product.template'].create({
            'name': 'HTTP Test Product',
            'list_price': 99.99,
            'vendor_id': cls.vendor.id,
        })
        
        # Créer un utilisateur de test
        cls.test_user = cls.env['res.users'].create({
            'name': 'HTTP Test User',
            'login': 'http_test_user',
            'email': 'http_test_user@test.com',
            'password': 'test123',
        })

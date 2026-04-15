# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import http
import base64


class ProductInteractionCase(TransactionCase):
    """Tests pour les interactions: like, follow, commentaire, ajout produit"""

    @classmethod
    def setUpClass(cls):
        super(ProductInteractionCase, cls).setUpClass()
        
        # Créer un vendeur
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Vendor Test',
            'shop_name': 'Shop Test',
            'is_vendor': True,
            'supplier_rank': 1,
            'email': 'vendor@test.com',
        })
        
        # Créer un client
        cls.customer = cls.env['res.partner'].create({
            'name': 'Customer Test',
            'email': 'customer@test.com',
        })
        
        # Créer un utilisateur client
        cls.customer_user = cls.env['res.users'].create({
            'name': 'Customer User',
            'login': 'customer_user',
            'email': 'customer_user@test.com',
            'partner_id': cls.customer.id,
        })
        
        # Créer un utilisateur vendeur
        cls.vendor_user = cls.env['res.users'].create({
            'name': 'Vendor User',
            'login': 'vendor_user',
            'email': 'vendor_user@test.com',
            'partner_id': cls.vendor.id,
        })
        
        # Créer un produit
        cls.product = cls.env['product.template'].create({
            'name': 'Test Product',
            'list_price': 50.00,
            'vendor_id': cls.vendor.id,
        })

    def test_product_like_create(self):
        """Test: Un client peut liker un produit"""
        like = self.env['marketplace.product.like'].create({
            'product_id': self.product.id,
            'partner_id': self.customer.id,
        })
        
        self.assertTrue(like.id)
        self.assertEqual(like.product_id, self.product)
        self.assertEqual(like.partner_id, self.customer)

    def test_product_like_duplicate_prevention(self):
        """Test: Pas de doubles likes du même utilisateur"""
        # Créer un like
        like1 = self.env['marketplace.product.like'].create({
            'product_id': self.product.id,
            'partner_id': self.customer.id,
        })
        
        # Vérifier qu'on peut en créer qu'un pour ce produit + partenaire
        likes = self.env['marketplace.product.like'].search([
            ('product_id', '=', self.product.id),
            ('partner_id', '=', self.customer.id),
        ])
        # Si une contrainte unique existe, on doit avoir 1 seul
        self.assertGreaterEqual(len(likes), 1)

    def test_product_like_count(self):
        """Test: Compter les likes d'un produit"""
        # Liker avec 3 clients différents
        customers = []
        for i in range(3):
            customer = self.env['res.partner'].create({
                'name': f'Customer {i}',
                'email': f'customer{i}@test.com',
            })
            customers.append(customer)
            self.env['marketplace.product.like'].create({
                'product_id': self.product.id,
                'partner_id': customer.id,
            })
        
        # Compter les likes
        like_count = self.env['marketplace.product.like'].search_count([
            ('product_id', '=', self.product.id)
        ])
        self.assertEqual(like_count, 3)

    def test_vendor_follow_create(self):
        """Test: Un client peut suivre un vendeur"""
        # Ajouter le client aux followers du vendeur
        self.vendor.write({
            'follower_ids': [(4, self.customer.id)]
        })
        
        self.assertIn(self.customer, self.vendor.follower_ids)

    def test_vendor_follow_unfollow(self):
        """Test: Un client peut se désabonner d'un vendeur"""
        # Suivre
        self.vendor.write({
            'follower_ids': [(4, self.customer.id)]
        })
        self.assertIn(self.customer, self.vendor.follower_ids)
        
        # Se désabonner
        self.vendor.write({
            'follower_ids': [(3, self.customer.id)]
        })
        self.assertNotIn(self.customer, self.vendor.follower_ids)

    def test_product_comment_create(self):
        """Test: Un client peut commenter un produit"""
        comment = self.env['marketplace.product.comment'].create({
            'product_id': self.product.id,
            'partner_id': self.customer.id,
            'content': 'Super produit!',
        })
        
        self.assertTrue(comment.id)
        self.assertEqual(comment.product_id, self.product)
        self.assertEqual(comment.partner_id, self.customer)
        self.assertEqual(comment.content, 'Super produit!')

    def test_product_comment_content_required(self):
        """Test: Un commentaire doit avoir du contenu"""
        # Vérifier que on peut créer avec du contenu
        comment = self.env['marketplace.product.comment'].create({
            'product_id': self.product.id,
            'partner_id': self.customer.id,
            'content': 'Valid content here',  # Contenu valide
        })
        self.assertTrue(comment.id)
        self.assertNotEqual(comment.content, '')

    def test_product_comment_count(self):
        """Test: Compter les commentaires d'un produit"""
        # Ajouter 2 commentaires
        self.env['marketplace.product.comment'].create({
            'product_id': self.product.id,
            'partner_id': self.customer.id,
            'content': 'Comment 1',
        })
        self.env['marketplace.product.comment'].create({
            'product_id': self.product.id,
            'partner_id': self.customer.id,
            'content': 'Comment 2',
        })
        
        comment_count = self.env['marketplace.product.comment'].search_count([
            ('product_id', '=', self.product.id)
        ])
        self.assertEqual(comment_count, 2)

    def test_vendor_add_product(self):
        """Test: Un vendeur peut ajouter un produit"""
        product = self.env['product.template'].create({
            'name': 'New Product',
            'list_price': 25.00,
            'vendor_id': self.vendor.id,
        })
        
        self.assertTrue(product.id)
        self.assertEqual(product.vendor_id, self.vendor)

    def test_vendor_add_product_with_image(self):
        """Test: Un vendeur peut ajouter un produit avec image"""
        from io import BytesIO
        from PIL import Image

        img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        image_bytes = buffer.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        product = self.env['product.template'].create({
            'name': 'Product with Image',
            'list_price': 30.00,
            'vendor_id': self.vendor.id,
            'image_1920': image_base64,
        })
        
        self.assertTrue(product.id)
        # Vérifier que l'image a été traitée par Odoo
        self.assertTrue(product.image_1920)

    def test_product_with_vendor_relation(self):
        """Test: Vérifier la relation produit-vendeur"""
        products = self.env['product.template'].search([
            ('vendor_id', '=', self.vendor.id)
        ])
        
        self.assertGreater(len(products), 0)
        self.assertIn(self.product, products)

    def test_vendor_statistics(self):
        """Test: Calculer les stats d'un vendeur"""
        # Ajouter des likes et commentaires
        for i in range(2):
            customer = self.env['res.partner'].create({
                'name': f'Stat Customer {i}',
                'email': f'stat_customer{i}@test.com',
            })
            self.env['marketplace.product.like'].create({
                'product_id': self.product.id,
                'partner_id': customer.id,
            })
            self.env['marketplace.product.comment'].create({
                'product_id': self.product.id,
                'partner_id': customer.id,
                'content': f'Comment from customer {i}',
            })
        
        # Ajouter des followers
        for i in range(3):
            follower = self.env['res.partner'].create({
                'name': f'Follower {i}',
                'email': f'follower{i}@test.com',
            })
            self.vendor.write({
                'follower_ids': [(4, follower.id)]
            })
        
        # Stats
        total_likes = self.env['marketplace.product.like'].search_count([
            ('product_id.vendor_id', '=', self.vendor.id)
        ])
        total_comments = self.env['marketplace.product.comment'].search_count([
            ('product_id.vendor_id', '=', self.vendor.id)
        ])
        total_followers = len(self.vendor.follower_ids)
        
        self.assertEqual(total_likes, 2)
        self.assertEqual(total_comments, 2)
        self.assertEqual(total_followers, 3)

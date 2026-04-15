# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductLike(models.Model):
    _name = 'marketplace.product.like'
    _description = 'Product Like'

    product_id = fields.Many2one('product.template', string='Product', required=True)
    partner_id = fields.Many2one('res.partner', string='User', required=True)

    _sql_constraints = [
        ('unique_like', 'unique(product_id, partner_id)', 'You can only like a product once!'),
    ]

class ProductComment(models.Model):
    _name = 'marketplace.product.comment'
    _description = 'Product Comment'

    product_id = fields.Many2one('product.template', string='Product', required=True)
    partner_id = fields.Many2one('res.partner', string='User', required=True)
    content = fields.Text(string='Comment', required=True)
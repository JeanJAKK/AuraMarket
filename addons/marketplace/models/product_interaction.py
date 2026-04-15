# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductLike(models.Model):
    _name = 'marketplace.product.like'
    _description = 'Like produit'
    _sql_constraints = [
        ('unique_like', 'UNIQUE(product_id, partner_id)', 'Un seul like par produit par utilisateur.')
    ]

    product_id = fields.Many2one('product.template', string="Produit", required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Utilisateur", required=True, ondelete='cascade')


class ProductComment(models.Model):
    _name = 'marketplace.product.comment'
    _description = 'Commentaire produit'
    _order = 'date_comment desc'

    product_id = fields.Many2one('product.template', string="Produit", required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Auteur", required=True, ondelete='cascade')
    content = fields.Text(string="Commentaire", required=True)
    date_comment = fields.Datetime(string="Date", default=fields.Datetime.now)

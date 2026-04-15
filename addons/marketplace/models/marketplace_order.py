# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MarketplaceOrder(models.Model):
    _name = 'marketplace.order'
    _description = 'Commande Marketplace'
    _order = 'date_order desc'

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('marketplace.order')
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string="Commande origine",
        ondelete='cascade'
    )
    vendor_id = fields.Many2one(
        'res.partner',
        string="Vendeur",
        required=True,
        domain="[('is_vendor', '=', True)]"
    )
    customer_id = fields.Many2one(
        'res.partner',
        string="Client",
        required=True
    )
    date_order = fields.Datetime(
        string="Date",
        default=fields.Datetime.now
    )
    state = fields.Selection([
        ('draft',     'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('paid',      'Payée'),
        ('shipped',   'Expédiée'),
        ('done',      'Terminée'),
        ('cancelled', 'Annulée'),
    ], string="Statut", default='draft')

    line_ids = fields.One2many(
        'marketplace.order.line',
        'order_id',
        string="Lignes"
    )

    # Commissions
    commission_rate = fields.Float(
        string="Taux commission (%)",
        default=10.0
    )
    amount_total = fields.Float(
        string="Total",
        compute='_compute_amounts',
        store=True
    )
    amount_commission = fields.Float(
        string="Commission plateforme",
        compute='_compute_amounts',
        store=True
    )
    amount_vendor = fields.Float(
        string="Montant vendeur",
        compute='_compute_amounts',
        store=True
    )

    # Paiement (simulé)
    payment_state = fields.Selection([
        ('pending',  'En attente'),
        ('paid',     'Payé'),
        ('refunded', 'Remboursé'),
    ], string="Paiement", default='pending')
    payment_date = fields.Datetime(string="Date paiement")
    payment_ref  = fields.Char(string="Référence paiement")

    @api.depends('line_ids.subtotal', 'commission_rate')
    def _compute_amounts(self):
        for order in self:
            total = sum(order.line_ids.mapped('subtotal'))
            commission = round(total * order.commission_rate / 100, 2)
            order.amount_total      = total
            order.amount_commission = commission
            order.amount_vendor     = round(total - commission, 2)


class MarketplaceOrderLine(models.Model):
    _name = 'marketplace.order.line'
    _description = 'Ligne de commande Marketplace'

    order_id = fields.Many2one(
        'marketplace.order',
        string="Commande",
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.template',
        string="Produit",
        required=True
    )
    quantity   = fields.Float(string="Quantité", default=1.0)
    unit_price = fields.Float(string="Prix unitaire")
    subtotal   = fields.Float(
        string="Sous-total",
        compute='_compute_subtotal',
        store=True
    )

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = round(line.quantity * line.unit_price, 2)


class MarketplaceCart(models.Model):
    _name = 'marketplace.cart'
    _description = 'Panier marketplace'

    partner_id = fields.Many2one(
        'res.partner',
        string="Client",
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.template',
        string="Produit",
        required=True,
        ondelete='cascade'
    )
    quantity = fields.Integer(string="Quantité", default=1)

    _sql_constraints = [
        ('unique_cart_item', 'UNIQUE(partner_id, product_id)',
         'Un seul enregistrement par produit par client.')
    ]

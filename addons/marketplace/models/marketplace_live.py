# -*- coding: utf-8 -*-
from odoo import models, fields, api
import secrets


class MarketplaceLive(models.Model):
    _name = 'marketplace.live'
    _description = 'Session Live Shopping'
    _order = 'start_time desc'

    name = fields.Char(string="Titre du live", required=True)
    vendor_id = fields.Many2one(
        'res.partner', string="Vendeur",
        required=True, domain="[('is_vendor','=',True)]"
    )
    status = fields.Selection([
        ('scheduled', 'Programme'),
        ('live',      'En direct'),
        ('ended',     'Termine'),
    ], string="Statut", default='scheduled')

    start_time  = fields.Datetime(string="Debut")
    end_time    = fields.Datetime(string="Fin")
    description = fields.Text(string="Description")
    stream_key  = fields.Char(string="Cle stream", readonly=True)
    viewer_count = fields.Integer(string="Spectateurs", default=0)

    # Stats
    like_count    = fields.Integer(string="Likes", default=0)
    comment_count = fields.Integer(string="Commentaires", default=0)
    order_count   = fields.Integer(string="Commandes", default=0)
    revenue_total = fields.Float(string="Revenu total", default=0.0)

    # Relations
    product_ids = fields.One2many(
        'marketplace.live.product', 'live_id', string="Produits"
    )
    comment_ids = fields.One2many(
        'marketplace.live.comment', 'live_id', string="Commentaires"
    )
    reaction_ids = fields.One2many(
        'marketplace.live.reaction', 'live_id', string="Reactions"
    )
    order_ids = fields.One2many(
        'marketplace.live.order', 'live_id', string="Commandes"
    )

    def action_start(self):
        self.write({
            'status':     'live',
            'start_time': fields.Datetime.now(),
            'stream_key': secrets.token_hex(16),
        })

    def action_end(self):
        self.write({
            'status':   'ended',
            'end_time': fields.Datetime.now(),
        })

    @api.model
    def get_active_lives(self):
        return self.search([('status', '=', 'live')])


class MarketplaceLiveProduct(models.Model):
    _name = 'marketplace.live.product'
    _description = 'Produit mis en avant dans un live'

    live_id = fields.Many2one(
        'marketplace.live', string="Live",
        required=True, ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.template', string="Produit", required=True
    )
    is_featured   = fields.Boolean(string="En vedette", default=False)
    special_price = fields.Float(string="Prix live special")
    order_count   = fields.Integer(string="Commandes", default=0)
    sequence      = fields.Integer(string="Ordre", default=10)


class MarketplaceLiveComment(models.Model):
    _name = 'marketplace.live.comment'
    _description = 'Commentaire live'
    _order = 'create_date desc'

    live_id    = fields.Many2one('marketplace.live', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Auteur", required=True)
    content    = fields.Text(string="Commentaire", required=True)
    is_pinned  = fields.Boolean(string="Epingle", default=False)
    create_date = fields.Datetime(string="Date", readonly=True)


class MarketplaceLiveReaction(models.Model):
    _name = 'marketplace.live.reaction'
    _description = 'Reaction live'

    live_id    = fields.Many2one('marketplace.live', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Utilisateur")
    type       = fields.Selection([
        ('like',  'Like'),
        ('fire',  'Feu'),
        ('clap',  'Applaudissement'),
    ], string="Type", default='like')
    create_date = fields.Datetime(readonly=True)


class MarketplaceLiveOrder(models.Model):
    _name = 'marketplace.live.order'
    _description = 'Commande passee pendant un live'

    live_id  = fields.Many2one('marketplace.live', required=True, ondelete='cascade')
    order_id = fields.Many2one('marketplace.order', string="Commande", required=True)
    create_date = fields.Datetime(readonly=True)


class MarketplaceLiveViewer(models.Model):
    _name = 'marketplace.live.viewer'
    _description = 'Spectateur actif (heartbeat)'
    _order = 'last_seen desc'

    live_id = fields.Many2one(
        'marketplace.live', string='Live', required=True,
        ondelete='cascade', index=True
    )
    client_id = fields.Char(string='Client ID', required=True, index=True)
    partner_id = fields.Many2one('res.partner', string='Utilisateur')
    last_seen = fields.Datetime(
        string='Dernière activité', required=True,
        default=fields.Datetime.now, index=True
    )

    _sql_constraints = [
        ('unique_live_client', 'unique(live_id, client_id)', 'Client déjà présent pour ce live.'),
    ]

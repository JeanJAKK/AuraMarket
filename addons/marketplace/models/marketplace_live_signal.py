# -*- coding: utf-8 -*-
from odoo import models, fields


class MarketplaceLiveSignal(models.Model):
    _name = 'marketplace.live.signal'
    _description = 'Signal WebRTC (Live Shopping)'
    _order = 'id asc'

    live_id = fields.Many2one(
        'marketplace.live', string='Live', required=True,
        ondelete='cascade', index=True
    )

    sender = fields.Char(string='Sender', required=True, index=True)
    receiver = fields.Char(string='Receiver', required=True, index=True)

    kind = fields.Selection([
        ('offer', 'Offer'),
        ('answer', 'Answer'),
        ('ice', 'ICE'),
    ], string='Kind', required=True, index=True)

    payload = fields.Json(string='Payload')

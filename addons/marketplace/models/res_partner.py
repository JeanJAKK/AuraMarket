# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_vendor = fields.Boolean(
        string="Is a Vendor",
        default=False,
        help="Check this box if the partner is a marketplace seller."
    )
    shop_name = fields.Char(
        string="Shop Name",
        help="The public name of the vendor's shop."
    )
    follower_ids = fields.Many2many(
        'res.partner',
        'vendor_follower_rel',
        'vendor_id',
        'follower_id',
        string="Abonnés"
    )
    commission_rate = fields.Float(
    string="Taux de commission (%)",
    default=10.0,
    help="Pourcentage prélevé par la plateforme sur chaque vente."
   )
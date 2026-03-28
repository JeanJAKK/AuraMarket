from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendeur',
        domain=[('is_vendor', '=', True)],
        help="Vendeur associé à ce produit",
        tracking=True
    )
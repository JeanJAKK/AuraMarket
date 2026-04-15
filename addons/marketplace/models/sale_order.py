from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vendor_id = fields.Many2one('res.partner', string="Vendor")
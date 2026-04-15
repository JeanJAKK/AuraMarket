from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

     
    vendor_id = fields.Many2one(
    'res.partner',
    string="Vendor",
    domain="[('supplier_rank', '>', 0)]"
)
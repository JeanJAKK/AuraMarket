# -*- coding: utf-8 -*-
from odoo import models, api


class MarketplaceOrderService(models.AbstractModel):
    _name = 'marketplace.order.service'
    _description = 'Service de split des commandes marketplace'

    @api.model
    def split_sale_order(self, sale_order):
        """
        Éclate une sale.order en marketplace.order par vendeur.
        Retourne la liste des marketplace.order créés.
        """
        # Regrouper les lignes par vendeur
        lines_by_vendor = {}
        for line in sale_order.order_line:
            vendor = line.product_id.product_tmpl_id.vendor_id
            if not vendor:
                continue
            if vendor.id not in lines_by_vendor:
                lines_by_vendor[vendor.id] = {
                    'vendor': vendor,
                    'lines': []
                }
            lines_by_vendor[vendor.id]['lines'].append(line)

        marketplace_orders = []

        for vendor_id, data in lines_by_vendor.items():
            vendor  = data['vendor']
            lines   = data['lines']

            # Récupérer le taux de commission du vendeur (défaut 10%)
            commission_rate = getattr(vendor, 'commission_rate', 10.0)

            # Créer la marketplace.order
            order_vals = {
                'sale_order_id':   sale_order.id,
                'vendor_id':       vendor.id,
                'customer_id':     sale_order.partner_id.id,
                'commission_rate': commission_rate,
                'state':           'confirmed',
            }
            mp_order = self.env['marketplace.order'].create(order_vals)

            # Créer les lignes
            for line in lines:
                self.env['marketplace.order.line'].create({
                    'order_id':   mp_order.id,
                    'product_id': line.product_id.product_tmpl_id.id,
                    'quantity':   line.product_uom_qty,
                    'unit_price': line.price_unit,
                })

            marketplace_orders.append(mp_order)

        return marketplace_orders

    @api.model
    def simulate_payment(self, marketplace_order_id, ref=None):
        """
        Simule un paiement pour une marketplace.order.
        """
        from datetime import datetime
        order = self.env['marketplace.order'].browse(marketplace_order_id)
        if not order.exists():
            return False

        order.write({
            'payment_state': 'paid',
            'payment_date':  datetime.now(),
            'payment_ref':   ref or f'SIM-{order.name}',
            'state':         'paid',
        })
        return True

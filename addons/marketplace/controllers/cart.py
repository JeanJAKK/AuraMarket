# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class MarketplaceCartController(http.Controller):

    @http.route('/marketplace/cart', type='http', auth='user', website=True)
    def cart(self, **kw):
        partner = request.env.user.partner_id
        cart_items_raw = request.env['marketplace.cart'].sudo().search(
            [('partner_id', '=', partner.id)]
        )
        cart_items = []
        total = 0
        for item in cart_items_raw:
            subtotal = item.product_id.list_price * item.quantity
            total += subtotal
            cart_items.append({
                'product': item.product_id,
                'qty': item.quantity,
                'subtotal': round(subtotal, 2),
                'item_id': item.id,
            })
        return request.render('marketplace.cart_page', {
            'cart_items': cart_items,
            'total': round(total, 2),
        })

    @http.route('/marketplace/cart/add/<int:product_id>', type='http', auth='user', website=True)
    def cart_add(self, product_id, qty=1, **kw):
        partner = request.env.user.partner_id
        existing = request.env['marketplace.cart'].sudo().search([
            ('partner_id', '=', partner.id),
            ('product_id', '=', product_id),
        ], limit=1)
        if existing:
            existing.sudo().write({'quantity': existing.quantity + int(qty)})
        else:
            request.env['marketplace.cart'].sudo().create({
                'partner_id': partner.id,
                'product_id': product_id,
                'quantity': int(qty),
            })
        return request.redirect('/marketplace/cart')

    @http.route('/marketplace/cart/remove/<int:product_id>', type='http', auth='user', website=True)
    def cart_remove(self, product_id, **kw):
        partner = request.env.user.partner_id
        item = request.env['marketplace.cart'].sudo().search([
            ('partner_id', '=', partner.id),
            ('product_id', '=', product_id),
        ], limit=1)
        if item:
            item.sudo().unlink()
        return request.redirect('/marketplace/cart')

    @http.route('/marketplace/checkout', type='http', auth='user', website=True, methods=['POST'])
    def checkout(self, **kw):
        partner = request.env.user.partner_id
        cart_items = request.env['marketplace.cart'].sudo().search(
            [('partner_id', '=', partner.id)]
        )
        if not cart_items:
            return request.redirect('/marketplace/cart')

        order_lines = []
        for item in cart_items:
            p = item.product_id
            if p.exists() and p.product_variant_ids:
                order_lines.append((0, 0, {
                    'product_id': p.product_variant_ids[0].id,
                    'product_uom_qty': item.quantity,
                    'price_unit': p.list_price,
                }))

        if not order_lines:
            return request.redirect('/marketplace/cart')

        so = request.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'order_line': order_lines,
        })

        service = request.env['marketplace.order.service']
        mp_orders = service.split_sale_order(so)

        for o in mp_orders:
            service.simulate_payment(o.id, ref=f'WEB-{so.name}')

        notif = request.env['marketplace.notification']
        for o in mp_orders:
            notif.notify_vendor_new_order(o)
        notif.notify_customer_order_confirmed(mp_orders, so)

        cart_items.sudo().unlink()

        return request.render('marketplace.checkout_success', {
            'sale_order': so,
            'mp_orders': mp_orders,
        })

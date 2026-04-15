# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class MarketplaceProductController(http.Controller):

    @http.route('/product/<int:product_id>/like', type='http', auth='user', website=True)
    def product_like(self, product_id, **kw):
        """Handle the like/unlike action on a product from the website."""
        product = request.env['product.template'].sudo().browse(product_id)
        if not product.exists():
            return request.not_found()

        partner = request.env.user.partner_id
        existing = request.env['marketplace.product.like'].sudo().search([
            ('product_id', '=', product_id),
            ('partner_id', '=', partner.id)
        ])
        if existing:
            existing.sudo().unlink()
        else:
            request.env['marketplace.product.like'].sudo().create({
                'product_id': product_id,
                'partner_id': partner.id,
            })

        vendor_id = product.vendor_id.id
        return request.redirect(f'/vendor/{vendor_id}')

    @http.route('/product/<int:product_id>/comment', type='http', auth='user',
                website=True, methods=['POST'])
    def product_comment(self, product_id, content='', **kw):
        """Handle the comment on a product from the website."""
        product = request.env['product.template'].sudo().browse(product_id)
        if not product.exists() or not content.strip():
            return request.redirect(f'/vendors/{product.vendor_id.id}')

        request.env['marketplace.product.comment'].sudo().create({
            'product_id': product_id,
            'partner_id': request.env.user.partner_id.id,
            'content': content.strip(),
        })
        return request.redirect(f'/vendor/{product.vendor_id.id}')

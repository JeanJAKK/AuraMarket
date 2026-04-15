# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class MarketplaceVendorController(http.Controller):

    @http.route('/vendors', type='http', auth='public', website=True)
    def vendor_list(self, search='', **kw):
        """Render a page containing a list of marketplace vendors."""
        domain = [('is_vendor', '=', True)]
        if search:
            vendor_ids = request.env['product.template'].sudo().search(
                [('name', 'ilike', search)]
            ).mapped('vendor_id').ids
            domain.append(('id', 'in', vendor_ids))
        vendors = request.env['res.partner'].sudo().search(domain)
        return request.render('marketplace.vendor_list', {
            'vendors': vendors,
            'search': search,
        })

    @http.route('/vendor/<int:vendor_id>', type='http', auth='public', website=True)
    def vendor_profile(self, vendor_id, **kw):
        """Render a profile page for a marketplace vendor."""
        vendor = request.env['res.partner'].sudo().browse(vendor_id)
        if not vendor.exists() or not vendor.is_vendor:
            return request.not_found()
        products = request.env['product.template'].sudo().search(
            [('vendor_id', '=', vendor_id)]
        )
        return request.render('marketplace.vendor_profile', {
            'vendor': vendor,
            'products': products,
        })

    @http.route('/vendors/search', type='http', auth='public', website=True)
    def vendor_search(self, search='', vendor_id=None, **kw):
        """Render search results page for marketplace vendors and products."""
        domain = [('is_vendor', '=', True)]
        if vendor_id:
            domain.append(('id', '=', int(vendor_id)))
        products_domain = [('vendor_id', 'in',
            request.env['res.partner'].sudo().search(domain).ids)]
        if search:
            products_domain.append(('name', 'ilike', search))
        products = request.env['product.template'].sudo().search(products_domain)
        vendors = request.env['res.partner'].sudo().search([('is_vendor', '=', True)])
        return request.render('marketplace.search_results', {
            'products': products,
            'vendors': vendors,
            'search': search,
            'selected_vendor_id': int(vendor_id) if vendor_id else None,
        })

    @http.route('/vendor/<int:vendor_id>/follow', type='http', auth='user', website=True)
    def vendor_follow(self, vendor_id, **kw):
        """Handle follow/unfollow action on a vendor."""
        vendor = request.env['res.partner'].sudo().browse(vendor_id)
        if not vendor.exists() or not vendor.is_vendor:
            return request.not_found()

        partner = request.env.user.partner_id

        if partner in vendor.follower_ids:
            vendor.sudo().write({
                'follower_ids': [(3, partner.id)]
            })
            action = 'unfollow'
        else:
            vendor.sudo().write({
                'follower_ids': [(4, partner.id)]
            })
            action = 'follow'

        if action == 'follow':
            notif = request.env['marketplace.notification']
            notif.notify_vendor_new_follower(vendor, partner)

        return request.redirect(f'/vendor/{vendor_id}')

    @http.route('/marketplace', type='http', auth='public', website=True)
    def marketplace_home(self, **kw):
        """Render the marketplace homepage."""
        vendors = request.env['res.partner'].sudo().search(
            [('is_vendor', '=', True)], limit=6
        )
        total_vendors = request.env['res.partner'].sudo().search_count(
            [('is_vendor', '=', True)]
        )
        total_products = request.env['product.template'].sudo().search_count(
            [('vendor_id', '!=', False)]
        )
        return request.render('marketplace.marketplace_home', {
            'vendors': vendors,
            'total_vendors': total_vendors,
            'total_products': total_products,
        })

    @http.route('/my/vendor/dashboard', type='http', auth='user', website=True)
    def vendor_dashboard(self, **kw):
        """Render the dashboard page for a vendor."""
        partner = request.env.user.partner_id
        if not partner.is_vendor:
            return request.redirect('/vendors')

        products = request.env['product.template'].sudo().search(
            [('vendor_id', '=', partner.id)]
        )

        product_stats = []
        for p in products:
            likes = request.env['marketplace.product.like'].sudo().search_count(
                [('product_id', '=', p.id)]
            )
            comments = request.env['marketplace.product.comment'].sudo().search_count(
                [('product_id', '=', p.id)]
            )
            product_stats.append({
                'product': p,
                'likes': likes,
                'comments': comments,
            })

        mp_orders = request.env['marketplace.order'].sudo().search(
            [('vendor_id', '=', partner.id)],
            order='date_order desc'
        )

        total_revenue = sum(mp_orders.mapped('amount_vendor'))
        total_commission = sum(mp_orders.mapped('amount_commission'))
        total_orders = len(mp_orders)
        paid_orders = mp_orders.filtered(lambda o: o.payment_state == 'paid')
        total_paid = sum(paid_orders.mapped('amount_vendor'))

        vendor_lives = request.env['marketplace.live'].sudo().search(
            [('vendor_id', '=', partner.id)], order='create_date desc, id desc', limit=20
        )

        return request.render('marketplace.vendor_dashboard', {
            'vendor': partner,
            'product_stats': product_stats,
            'total_followers': len(partner.follower_ids),
            'total_likes': sum(s['likes'] for s in product_stats),
            'total_comments': sum(s['comments'] for s in product_stats),
            'mp_orders': mp_orders,
            'total_revenue': round(total_revenue, 2),
            'total_commission': round(total_commission, 2),
            'total_orders': total_orders,
            'total_paid': round(total_paid, 2),
            'vendor_lives': vendor_lives,
        })

    @http.route('/my/vendor/product/new', type='http', auth='user', website=True,
                methods=['GET', 'POST'], csrf=False)
    def vendor_product_new(self, **kw):
        """Render a form for creating a new product as a vendor."""
        partner = request.env.user.partner_id
        if not partner.is_vendor:
            return request.redirect('/vendors')

        if request.httprequest.method == 'POST':
            name = kw.get('name', '').strip()
            price = kw.get('list_price', 0)
            description = kw.get('description', '').strip()

            image_data = None
            if 'image' in request.httprequest.files:
                image_file = request.httprequest.files['image']
                if image_file and image_file.filename:
                    image_data = image_file.read()

            if name:
                vals = {
                    'name': name,
                    'list_price': float(price) if price else 0.0,
                    'description_sale': description,
                    'vendor_id': partner.id,
                }
                if image_data:
                    import base64
                    vals['image_1920'] = base64.b64encode(image_data).decode('utf-8')

                request.env['product.template'].sudo().create(vals)
            return request.redirect('/my/vendor/dashboard')

        return request.render('marketplace.vendor_product_form', {
            'vendor': partner,
        })

    @http.route('/my/vendor/product/<int:product_id>/delete',
                type='http', auth='user', website=True)
    def vendor_product_delete(self, product_id, **kw):
        """Supprime un produit de la liste des produits du vendeur."""
        partner = request.env.user.partner_id
        product = request.env['product.template'].sudo().browse(product_id)
        if product.exists() and product.vendor_id.id == partner.id:
            product.sudo().unlink()
        return request.redirect('/my/vendor/dashboard')

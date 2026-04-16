# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import http, fields
from odoo.http import request


class MarketplaceLiveController(http.Controller):

    def _cleanup_webrtc_signals(self, live_id):
        cutoff = fields.Datetime.now() - timedelta(minutes=10)
        request.env['marketplace.live.signal'].sudo().search([
            ('live_id', '=', live_id),
            ('create_date', '<', cutoff),
        ]).unlink()

    def _track_live_viewer(self, live_id, client_id):
        client_id = (client_id or '').strip()
        if not client_id:
            return

        # Keep identifiers bounded to avoid abusive payloads.
        client_id = client_id[:80]

        Viewer = request.env['marketplace.live.viewer'].sudo()
        now = fields.Datetime.now()

        vals = {'last_seen': now}
        try:
            public_user = request.env.ref('base.public_user')
            if request.env.user.id != public_user.id:
                vals['partner_id'] = request.env.user.partner_id.id
        except Exception:
            # If ref fails for any reason, keep partner_id empty.
            pass

        viewer = Viewer.search([
            ('live_id', '=', live_id),
            ('client_id', '=', client_id),
        ], limit=1)

        if viewer:
            viewer.write(vals)
            return

        vals.update({'live_id': live_id, 'client_id': client_id})
        Viewer.create(vals)

    def _compute_live_viewer_count(self, live_id):
        cutoff = fields.Datetime.now() - timedelta(seconds=15)
        return request.env['marketplace.live.viewer'].sudo().search_count([
            ('live_id', '=', live_id),
            ('last_seen', '>=', cutoff),
        ])

    @http.route('/live', type='http', auth='public', website=True)
    def live_list(self, **kw):
        lives = request.env['marketplace.live'].sudo().search(
            [('status', 'in', ['live', 'scheduled', 'ended'])],
            order='start_time desc, id desc'
        )

        viewer_counts = {}
        if lives:
            cutoff = fields.Datetime.now() - timedelta(seconds=15)
            groups = request.env['marketplace.live.viewer'].sudo().read_group(
                [('live_id', 'in', lives.ids), ('last_seen', '>=', cutoff)],
                ['live_id'],
                ['live_id'],
            )
            for g in groups:
                live_field = g.get('live_id')
                if live_field and isinstance(live_field, (list, tuple)) and live_field[0]:
                    viewer_counts[live_field[0]] = g.get('live_id_count', 0)

        return request.render('marketplace.live_list', {
            'lives': lives,
            'viewer_counts': viewer_counts,
        })

    @http.route('/live/<int:live_id>', type='http', auth='public', website=True)
    def live_watch(self, live_id, **kw):
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists():
            return request.not_found()
        comments = request.env['marketplace.live.comment'].sudo().search(
            [('live_id', '=', live_id)], order='create_date asc', limit=50
        )
        featured_products = request.env['marketplace.live.product'].sudo().search([
            ('live_id', '=', live_id),
            ('is_featured', '=', True),
        ], order='sequence asc, id desc')

        featured = featured_products[:1]

        vendor_products = request.env['product.template']
        is_broadcaster = False
        try:
            public_user = request.env.ref('base.public_user')
            if request.env.user.id != public_user.id and request.env.user.partner_id.id == live.vendor_id.id:
                is_broadcaster = True
        except Exception:
            is_broadcaster = False

        if is_broadcaster:
            vendor_products = request.env['product.template'].sudo().search([
                ('vendor_id', '=', live.vendor_id.id),
            ], order='name asc, id desc')

        last_reaction = request.env['marketplace.live.reaction'].sudo().search(
            [('live_id', '=', live_id)], order='id desc', limit=1
        )
        last_live_order = request.env['marketplace.live.order'].sudo().search(
            [('live_id', '=', live_id)], order='id desc', limit=1
        )
        return request.render('marketplace.live_watch', {
            'live': live,
            'comments': comments,
            'featured': featured,
            'featured_products': featured_products,
            'vendor_products': vendor_products,
            'last_reaction_id': last_reaction.id if last_reaction else 0,
            'last_order_id': last_live_order.id if last_live_order else 0,
        })

    @http.route('/my/vendor/live/new', type='http', auth='user', website=True,
                methods=['GET', 'POST'], csrf=False)
    def vendor_live_new(self, **kw):
        partner = request.env.user.partner_id
        if not partner.is_vendor:
            return request.redirect('/vendors')

        if request.httprequest.method == 'POST':
            title = kw.get('title', '').strip()
            description = kw.get('description', '').strip()
            if title:
                live = request.env['marketplace.live'].sudo().create({
                    'name': title,
                    'vendor_id': partner.id,
                    'description': description,
                    'status': 'scheduled',
                })
                return request.redirect(f'/my/vendor/live/{live.id}/dashboard')

        products = request.env['product.template'].sudo().search(
            [('vendor_id', '=', partner.id)]
        )
        return request.render('marketplace.live_new', {
            'vendor': partner,
            'products': products,
        })

    @http.route('/my/vendor/live/<int:live_id>/dashboard', type='http', auth='user', website=True)
    def vendor_live_dashboard(self, live_id, **kw):
        partner = request.env.user.partner_id
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists() or live.vendor_id.id != partner.id:
            return request.redirect('/my/vendor/dashboard')
        products = request.env['product.template'].sudo().search(
            [('vendor_id', '=', partner.id)]
        )

        live_orders = request.env['marketplace.live.order'].sudo().search(
            [('live_id', '=', live_id)], order='id desc', limit=20
        )
        last_order = live_orders[:1]

        last_reaction = request.env['marketplace.live.reaction'].sudo().search(
            [('live_id', '=', live_id)], order='id desc', limit=1
        )
        return request.render('marketplace.live_vendor_dashboard', {
            'live': live,
            'products': products,
            'partner': partner,
            'live_orders': live_orders,
            'last_order_id': last_order.id if last_order else 0,
            'last_reaction_id': last_reaction.id if last_reaction else 0,
        })

    @http.route('/my/vendor/live/<int:live_id>/start', type='http', auth='user',
                website=True, methods=['POST'], csrf=False)
    def vendor_live_start(self, live_id, **kw):
        partner = request.env.user.partner_id
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if live.exists() and live.vendor_id.id == partner.id:
            live.action_start()
        return request.redirect(f'/my/vendor/live/{live_id}/dashboard')

    @http.route('/my/vendor/live/<int:live_id>/start/json', type='json', auth='user', website=True, csrf=False)
    def vendor_live_start_json(self, live_id, **kw):
        partner = request.env.user.partner_id
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists() or live.vendor_id.id != partner.id:
            return {'status': 'forbidden'}

        live.action_start()
        return {
            'status': 'ok',
            'live': {
                'id': live.id,
                'status': live.status,
                'viewer_count': live.viewer_count,
                'like_count': live.like_count,
                'comment_count': live.comment_count,
                'order_count': live.order_count,
                'revenue_total': live.revenue_total,
            },
        }

    @http.route('/my/vendor/live/<int:live_id>/end', type='http', auth='user',
                website=True, methods=['POST'], csrf=False)
    def vendor_live_end(self, live_id, **kw):
        partner = request.env.user.partner_id
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if live.exists() and live.vendor_id.id == partner.id:
            live.action_end()
        return request.redirect('/my/vendor/dashboard')

    @http.route('/my/vendor/live/<int:live_id>/end/json', type='json', auth='user', website=True, csrf=False)
    def vendor_live_end_json(self, live_id, **kw):
        partner = request.env.user.partner_id
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists() or live.vendor_id.id != partner.id:
            return {'status': 'forbidden'}

        live.action_end()
        return {
            'status': 'ok',
            'live': {
                'id': live.id,
                'status': live.status,
                'viewer_count': live.viewer_count,
                'like_count': live.like_count,
                'comment_count': live.comment_count,
                'order_count': live.order_count,
                'revenue_total': live.revenue_total,
            },
        }

    @http.route('/my/vendor/live/<int:live_id>/feature/<int:product_id>',
                type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def vendor_live_feature(self, live_id, product_id, special_price=0, featured='1', **kw):
        partner = request.env.user.partner_id
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists() or live.vendor_id.id != partner.id:
            return request.redirect('/my/vendor/dashboard')

        target_is_featured = str(featured or '1').strip() not in ('0', 'false', 'False', 'no', 'off')

        existing = request.env['marketplace.live.product'].sudo().search(
            [('live_id', '=', live_id), ('product_id', '=', product_id)], limit=1
        )

        if existing:
            vals = {
                'is_featured': target_is_featured,
            }
            if target_is_featured:
                vals['special_price'] = float(special_price) if special_price else 0
            existing.sudo().write(vals)
        elif target_is_featured:
            request.env['marketplace.live.product'].sudo().create({
                'live_id': live_id,
                'product_id': product_id,
                'is_featured': True,
                'special_price': float(special_price) if special_price else 0,
            })

        ref = (request.httprequest.referrer or '').strip()
        if ref and ('/live/%s' % live_id) in ref:
            return request.redirect(f'/live/{live_id}')

        return request.redirect(f'/my/vendor/live/{live_id}/dashboard')

    @http.route('/my/vendor/live/<int:live_id>/feature/json', type='json', auth='user', website=True, csrf=False)
    def vendor_live_feature_json(self, live_id, product_id=None, special_price=0, featured=True, **kw):
        partner = request.env.user.partner_id
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists() or live.vendor_id.id != partner.id:
            return {'status': 'forbidden'}

        try:
            product_id_int = int(product_id or 0)
        except Exception:
            product_id_int = 0
        if product_id_int <= 0:
            return {'status': 'error', 'code': 'missing_product'}

        product = request.env['product.template'].sudo().browse(product_id_int)
        if not product.exists() or not product.vendor_id or product.vendor_id.id != partner.id:
            return {'status': 'error', 'code': 'product_not_allowed'}

        target_is_featured = bool(featured)
        existing = request.env['marketplace.live.product'].sudo().search([
            ('live_id', '=', live_id),
            ('product_id', '=', product_id_int),
        ], order='id desc', limit=1)

        if existing:
            vals = {'is_featured': target_is_featured}
            if target_is_featured:
                vals['special_price'] = float(special_price) if special_price else 0
            existing.sudo().write(vals)
        elif target_is_featured:
            request.env['marketplace.live.product'].sudo().create({
                'live_id': live_id,
                'product_id': product_id_int,
                'is_featured': True,
                'special_price': float(special_price) if special_price else 0,
            })

        return {'status': 'ok'}

    @http.route('/live/<int:live_id>/comment', type='http', auth='user',
                website=True, methods=['POST'])
    def live_comment(self, live_id, content='', **kw):
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if live.exists() and content.strip():
            request.env['marketplace.live.comment'].sudo().create({
                'live_id': live_id,
                'partner_id': request.env.user.partner_id.id,
                'content': content.strip(),
            })
            live.sudo().write({'comment_count': live.comment_count + 1})
        return request.redirect(f'/live/{live_id}')

    @http.route('/live/<int:live_id>/comment/json', type='json', auth='user', website=True)
    def live_comment_json(self, live_id, content='', **kw):
        """Create a comment without reloading the live page."""
        live = request.env['marketplace.live'].sudo().browse(live_id)
        content = (content or '').strip()
        if not live.exists() or not content:
            return {'status': 'error'}

        comment = request.env['marketplace.live.comment'].sudo().create({
            'live_id': live_id,
            'partner_id': request.env.user.partner_id.id,
            'content': content,
        })
        new_comment_count = live.comment_count + 1
        live.sudo().write({'comment_count': new_comment_count})

        return {
            'status': 'ok',
            'comment': {
                'id': comment.id,
                'partner_name': comment.partner_id.name,
                'content': comment.content,
            },
            'live': {
                'id': live.id,
                'status': live.status,
                'viewer_count': live.viewer_count,
                'like_count': live.like_count,
                'comment_count': new_comment_count,
                'order_count': live.order_count,
            },
        }

    @http.route('/live/<int:live_id>/react', type='json', auth='user', website=True)
    def live_react(self, live_id, type='like', **kw):
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if live.exists():
            request.env['marketplace.live.reaction'].sudo().create({
                'live_id': live_id,
                'partner_id': request.env.user.partner_id.id,
                'type': type,
            })
            live.sudo().write({'like_count': live.like_count + 1})
        return {'status': 'ok'}

    @http.route('/live/<int:live_id>/featured', type='json', auth='public', website=True, csrf=False)
    def live_featured(self, live_id, **kw):
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists():
            return {'featured': False}

        featured_products = request.env['marketplace.live.product'].sudo().search([
            ('live_id', '=', live_id),
            ('is_featured', '=', True),
        ], order='sequence asc, id desc')

        if not featured_products:
            return {'featured': False}

        products_payload = []
        for fp in featured_products:
            product = fp.product_id
            if not product:
                continue
            products_payload.append({
                'id': product.id,
                'name': product.name,
                'list_price': product.list_price,
                'special_price': fp.special_price or 0,
            })

        first = products_payload[0] if products_payload else None
        return {
            'featured': True,
            'products': products_payload,
            # Backward compatible payload (first featured product)
            'product': first or {},
        }

    @http.route('/live/<int:live_id>/buy', type='json', auth='user', website=True, csrf=False)
    def live_buy(self, live_id, product_id=None, qty=1, **kw):
        """Purchase a product from a live without leaving the live page.

        Creates a sale.order, splits it into marketplace.order(s) (per vendor), simulates payment,
        and links the resulting order(s) to the live via marketplace.live.order.
        """
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists():
            return {'status': 'not_found'}

        if live.status != 'live':
            return {'status': 'error', 'code': 'live_not_active'}

        try:
            product_id_int = int(product_id or 0)
        except Exception:
            product_id_int = 0

        try:
            qty_int = int(qty or 1)
        except Exception:
            qty_int = 1

        if product_id_int <= 0:
            return {'status': 'error', 'code': 'missing_product'}

        qty_int = max(1, min(qty_int, 99))

        product = request.env['product.template'].sudo().browse(product_id_int)
        if not product.exists():
            return {'status': 'error', 'code': 'product_not_found'}

        # Safety: only allow buying products from the live's vendor.
        if not product.vendor_id or product.vendor_id.id != live.vendor_id.id:
            return {'status': 'error', 'code': 'product_not_allowed'}

        if not product.product_variant_ids:
            return {'status': 'error', 'code': 'product_no_variant'}

        # Use a live special price if set for this product.
        live_product = request.env['marketplace.live.product'].sudo().search([
            ('live_id', '=', live_id),
            ('product_id', '=', product_id_int),
        ], order='id desc', limit=1)

        unit_price = product.list_price
        if live_product and live_product.special_price and live_product.special_price > 0:
            unit_price = live_product.special_price

        partner = request.env.user.partner_id
        so = request.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': product.product_variant_ids[0].id,
                'product_uom_qty': qty_int,
                'price_unit': unit_price,
            })],
        })

        service = request.env['marketplace.order.service']
        mp_orders = service.split_sale_order(so)
        if not mp_orders:
            return {'status': 'error', 'code': 'split_failed'}

        for o in mp_orders:
            service.simulate_payment(o.id, ref=f'LIVE-{live.id}-{so.name}')

        notif = request.env['marketplace.notification']
        for o in mp_orders:
            notif.notify_vendor_new_order(o)
        notif.notify_customer_order_confirmed(mp_orders, so)

        # Link to the live + update live stats.
        total_vendor_amount = 0.0
        for o in mp_orders:
            total_vendor_amount += o.amount_vendor
            request.env['marketplace.live.order'].sudo().create({
                'live_id': live.id,
                'order_id': o.id,
            })

        if live_product:
            live_product.sudo().write({'order_count': live_product.order_count + 1})

        live.sudo().write({
            'order_count': live.order_count + len(mp_orders),
            'revenue_total': live.revenue_total + total_vendor_amount,
        })

        # Return a compact payload for the popup.
        first_order = mp_orders[0]
        first_line = first_order.line_ids[:1]
        return {
            'status': 'ok',
            'sale_order': {'id': so.id, 'name': so.name},
            'order': {
                'id': first_order.id,
                'name': first_order.name,
                'amount_total': first_order.amount_total,
                'amount_vendor': first_order.amount_vendor,
                'product_name': first_line.product_id.name if first_line else product.name,
                'qty': first_line.quantity if first_line else qty_int,
            },
            'live': {
                'id': live.id,
                'status': live.status,
                'viewer_count': self._compute_live_viewer_count(live.id),
                'like_count': live.like_count,
                'comment_count': live.comment_count,
                'order_count': live.order_count,
                'revenue_total': live.revenue_total,
            },
        }

    @http.route('/live/<int:live_id>/updates', type='json', auth='public', website=True, csrf=False)
    def live_updates(self, live_id, after_comment_id=0, after_reaction_id=0, after_order_id=0, client_id=None, limit=50, **kw):
        """Poll live state + new comments.

        Used by the frontend to update comments/reactions/status without reloading.
        """
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists():
            return {
                'status': 'not_found',
                'live': False,
                'comments': [],
                'reactions': [],
                'orders': [],
            }

        try:
            after_comment_id = int(after_comment_id or 0)
        except Exception:
            after_comment_id = 0

        try:
            after_reaction_id = int(after_reaction_id or 0)
        except Exception:
            after_reaction_id = 0

        try:
            after_order_id = int(after_order_id or 0)
        except Exception:
            after_order_id = 0

        try:
            limit = int(limit or 50)
        except Exception:
            limit = 50

        limit = max(1, min(limit, 100))

        comments = request.env['marketplace.live.comment'].sudo().search([
            ('live_id', '=', live_id),
            ('id', '>', after_comment_id),
        ], order='id asc', limit=limit)

        reactions = request.env['marketplace.live.reaction'].sudo().search([
            ('live_id', '=', live_id),
            ('id', '>', after_reaction_id),
        ], order='id asc', limit=limit)

        live_orders = request.env['marketplace.live.order'].sudo().search([
            ('live_id', '=', live_id),
            ('id', '>', after_order_id),
        ], order='id asc', limit=limit)

        # Viewer heartbeat + computed count.
        if client_id:
            self._track_live_viewer(live_id, client_id)
        viewer_count = self._compute_live_viewer_count(live_id)

        return {
            'status': 'ok',
            'live': {
                'id': live.id,
                'status': live.status,
                'viewer_count': viewer_count,
                'like_count': live.like_count,
                'comment_count': live.comment_count,
                'order_count': live.order_count,
                'revenue_total': live.revenue_total,
            },
            'comments': [{
                'id': c.id,
                'partner_name': c.partner_id.name,
                'content': c.content,
            } for c in comments],
            'reactions': [{
                'id': r.id,
                'type': r.type,
            } for r in reactions],
            'orders': [{
                'id': lo.id,
                'buyer_name': lo.order_id.customer_id.name,
                'amount_total': lo.order_id.amount_total,
                'product_name': (lo.order_id.line_ids[:1].product_id.name or '') if lo.order_id.line_ids else '',
            } for lo in live_orders],
        }

    @http.route('/live/<int:live_id>/webrtc/signal', type='json', auth='public', website=True, csrf=False)
    def live_webrtc_signal(self, live_id, sender=None, receiver=None, kind=None, payload=None, **kw):
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists():
            return {'status': 'not_found'}

        sender = (sender or '').strip()
        receiver = (receiver or '').strip()
        kind = (kind or '').strip()

        if not sender or not receiver or kind not in {'offer', 'answer', 'ice'}:
            return {'status': 'error'}

        request.env['marketplace.live.signal'].sudo().create({
            'live_id': live_id,
            'sender': sender,
            'receiver': receiver,
            'kind': kind,
            'payload': payload or {},
        })
        self._cleanup_webrtc_signals(live_id)
        return {'status': 'ok'}

    @http.route('/live/<int:live_id>/webrtc/poll', type='json', auth='public', website=True, csrf=False)
    def live_webrtc_poll(self, live_id, receiver=None, after_id=0, limit=50, **kw):
        live = request.env['marketplace.live'].sudo().browse(live_id)
        if not live.exists():
            return {'messages': []}

        receiver = (receiver or '').strip()
        if not receiver:
            return {'messages': []}

        try:
            after_id = int(after_id or 0)
        except Exception:
            after_id = 0

        try:
            limit = int(limit or 50)
        except Exception:
            limit = 50

        limit = max(1, min(limit, 100))

        signals = request.env['marketplace.live.signal'].sudo().search([
            ('live_id', '=', live_id),
            ('receiver', '=', receiver),
            ('id', '>', after_id),
        ], order='id asc', limit=limit)

        messages = [{
            'id': s.id,
            'sender': s.sender,
            'kind': s.kind,
            'payload': s.payload or {},
        } for s in signals]

        signals.sudo().unlink()
        self._cleanup_webrtc_signals(live_id)
        return {'messages': messages}

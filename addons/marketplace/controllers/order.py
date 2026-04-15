# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class MarketplaceOrderController(http.Controller):

    @http.route('/marketplace/order/<int:order_id>/messages', type='http', auth='user', website=True)
    def order_messages(self, order_id, **kw):
        """Render the messages page for a marketplace.order."""
        partner = request.env.user.partner_id
        order = request.env['marketplace.order'].sudo().browse(order_id)

        if not order.exists():
            return request.not_found()

        if partner.id not in [order.customer_id.id, order.vendor_id.id]:
            return request.redirect('/my/vendor/dashboard')

        messages = request.env['marketplace.message'].sudo().search(
            [('order_id', '=', order_id)],
            order='create_date asc'
        )
        unread = messages.filtered(
            lambda m: m.receiver_id.id == partner.id and not m.is_read
        )
        unread.sudo().write({'is_read': True})

        return request.render('marketplace.order_messages', {
            'order': order,
            'messages': messages,
            'partner': partner,
        })

    @http.route('/marketplace/order/<int:order_id>/message/send',
                type='http', auth='user', website=True, methods=['POST'])
    def order_message_send(self, order_id, content='', **kw):
        """Envoie un message sur une commande."""
        partner = request.env.user.partner_id
        order = request.env['marketplace.order'].sudo().browse(order_id)

        if not order.exists() or not content.strip():
            return request.redirect(f'/marketplace/order/{order_id}/messages')

        if partner.id == order.customer_id.id:
            receiver = order.vendor_id
        else:
            receiver = order.customer_id

        request.env['marketplace.message'].sudo().create({
            'order_id': order_id,
            'sender_id': partner.id,
            'receiver_id': receiver.id,
            'content': content.strip(),
        })

        if receiver.user_ids:
            request.env['marketplace.notification'].sudo().notify(
                user_id=receiver.user_ids[0].id,
                title=f"Nouveau message — {order.name}",
                message=f"De : {partner.name}\n{content.strip()[:100]}",
                notif_type='order'
            )

        return request.redirect(f'/marketplace/order/{order_id}/messages')


class MarketplaceNotificationController(http.Controller):

    @http.route('/my/notifications', type='http', auth='user', website=True)
    def my_notifications(self, **kw):
        """Render the notifications page for the current user."""
        notifs = request.env['marketplace.notification'].sudo().search(
            [('user_id', '=', request.env.user.id)],
            order='create_date desc',
            limit=50
        )
        notifs.filtered(lambda n: not n.is_read).sudo().write({'is_read': True})
        return request.render('marketplace.notifications_page', {
            'notifications': notifs,
        })

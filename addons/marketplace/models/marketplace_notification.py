# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MarketplaceNotification(models.Model):
    _name = 'marketplace.notification'
    _description = 'Notification interne marketplace'
    _order = 'create_date desc'

    user_id = fields.Many2one(
        'res.users',
        string="Destinataire",
        required=True,
        ondelete='cascade'
    )
    title = fields.Char(string="Titre", required=True)
    message = fields.Text(string="Message", required=True)
    type = fields.Selection([
        ('order',  'Commande'),
        ('system', 'Système'),
        ('social', 'Social'),
    ], string="Type", default='system')
    is_read = fields.Boolean(string="Lu", default=False)
    create_date = fields.Datetime(string="Date", readonly=True)

    def mark_as_read(self):
        self.write({'is_read': True})

    @api.model
    def notify(self, user_id, title, message, notif_type='system'):
        """Créer une notification pour un utilisateur."""
        return self.create({
            'user_id': user_id,
            'title':   title,
            'message': message,
            'type':    notif_type,
        })

    @api.model
    def notify_vendor_new_order(self, mp_order):
        """Notifier le vendeur d'une nouvelle commande."""
        vendor = mp_order.vendor_id
        if not vendor.user_ids:
            return False
        vendor_user = vendor.user_ids[0]
        lines_text = ", ".join([
            f"{l.product_id.name} x{l.quantity}"
            for l in mp_order.line_ids
        ])
        return self.notify(
            user_id=vendor_user.id,
            title=f"Nouvelle commande {mp_order.name}",
            message=f"Client : {mp_order.customer_id.name}\nProduits : {lines_text}\nMontant : {mp_order.amount_vendor} FCFA (après commission)",
            notif_type='order'
        )

    @api.model
    def notify_customer_order_confirmed(self, mp_orders, sale_order):
        """Notifier le client que sa commande est confirmée."""
        customer = sale_order.partner_id
        if not customer.user_ids:
            return False
        customer_user = customer.user_ids[0]
        vendors = ", ".join([
            o.vendor_id.shop_name or o.vendor_id.name
            for o in mp_orders
        ])
        total = sum(o.amount_total for o in mp_orders)
        return self.notify(
            user_id=customer_user.id,
            title=f"Commande {sale_order.name} confirmée !",
            message=f"Vendeurs : {vendors}\nTotal payé : {total} FCFA",
            notif_type='order'
        )

    @api.model
    def notify_vendor_new_follower(self, vendor, follower):
        """Notifier le vendeur d'un nouvel abonné."""
        if not vendor.user_ids:
            return False
        vendor_user = vendor.user_ids[0]
        return self.notify(
            user_id=vendor_user.id,
            title="Nouvel abonné !",
            message=f"{follower.name} suit maintenant votre boutique.\nTotal abonnés : {len(vendor.follower_ids)}",
            notif_type='social'
        )


class MarketplaceMessage(models.Model):
    _name = 'marketplace.message'
    _description = 'Message marketplace lié à une commande'
    _order = 'create_date asc'

    order_id = fields.Many2one(
        'marketplace.order',
        string="Commande",
        required=True,
        ondelete='cascade'
    )
    sender_id = fields.Many2one(
        'res.partner',
        string="Expéditeur",
        required=True,
        ondelete='cascade'
    )
    receiver_id = fields.Many2one(
        'res.partner',
        string="Destinataire",
        required=True,
        ondelete='cascade'
    )
    content = fields.Text(string="Message", required=True)
    create_date = fields.Datetime(string="Date", readonly=True)
    is_read = fields.Boolean(string="Lu", default=False)

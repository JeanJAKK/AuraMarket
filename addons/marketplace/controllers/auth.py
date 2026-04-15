# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class MarketplaceAuthController(http.Controller):

    @http.route('/register', type='http', auth='public', website=True, methods=['GET'])
    def register_page(self, **kw):
        """Render the registration page."""
        if request.env.user.id != request.env.ref('base.public_user').id:
            return request.redirect('/marketplace')
        return request.render('marketplace.register_page', {})

    @http.route('/register', type='http', auth='public', website=True,
                methods=['POST'], csrf=False)
    def register_submit(self, name='', email='', password='', role='customer', **kw):
        errors = []
        if not name.strip():
            errors.append("Le nom est requis.")
        if not email.strip() or '@' not in email:
            errors.append("Email invalide.")
        if len(password) < 6:
            errors.append("Mot de passe trop court (6 caracteres minimum).")

        existing = request.env['res.users'].sudo().search(
            [('login', '=', email.strip())], limit=1
        )
        if existing:
            errors.append("Cet email est deja utilise.")

        if errors:
            return request.render('marketplace.register_page', {
                'errors': errors,
                'name': name,
                'email': email,
                'role': role,
            })

        user = request.env['res.users'].sudo().create({
            'name': name.strip(),
            'login': email.strip(),
            'email': email.strip(),
            'password': password,
            'groups_id': [(4, request.env.ref('base.group_portal').id)],
        })

        if role == 'vendor':
            user.partner_id.sudo().write({
                'is_vendor': True,
                'shop_name': name.strip(),
            })

        request.env['marketplace.notification'].sudo().notify(
            user_id=user.id,
            title="Bienvenue sur MarketHub !",
            message=(
                f"Bonjour {name.strip()}, votre compte "
                f"{'vendeur' if role == 'vendor' else 'client'} a ete cree."
            ),
            notif_type='system'
        )

        try:
            uid = request.session.authenticate(
                request.env.cr.dbname,
                email.strip(),
                password
            )
            if uid:
                return request.redirect('/marketplace')
        except Exception:
            pass

        return request.redirect('/web/login?login=' + email.strip())

    @http.route('/', type='http', auth='public', website=True)
    def home(self, **kw):
        return request.redirect('/marketplace')

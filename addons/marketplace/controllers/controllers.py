# -*- coding: utf-8 -*-
# from odoo import http


# class Marketplace(http.Controller):
#     @http.route('/marketplace/marketplace', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/marketplace/marketplace/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('marketplace.listing', {
#             'root': '/marketplace/marketplace',
#             'objects': http.request.env['marketplace.marketplace'].search([]),
#         })

#     @http.route('/marketplace/marketplace/objects/<model("marketplace.marketplace"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('marketplace.object', {
#             'object': obj
#         })


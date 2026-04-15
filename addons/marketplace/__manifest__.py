# -*- coding: utf-8 -*-
{
    'name': "Marketplace Multi-Vendeurs",
    'summary': "Gestion de marketplace multi-vendeurs avec produits et commandes",
    'description': """
Module marketplace permettant à plusieurs vendeurs de gérer leurs produits
et de recevoir des commandes depuis une plateforme commune.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'license': 'LGPL-3',

    'category': 'Sales',
    'version': '1.0',

    'depends': [
        'base',
        'product',
        'sale',
        'sale_management',
        'portal',
        'website',
    ],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',

        'views/product_view.xml',
        'views/templates_vendor.xml',
        'views/templates_search.xml',
        'views/templates_cart.xml',
        'views/templates_order.xml',
        'views/templates_auth.xml',
        'views/templates_live.xml',
        'views/res_partner_views.xml',
        'views/menus.xml',
        'views/website_customize.xml',
    ],

    'assets': {
    'web.assets_frontend': [
        'marketplace/static/src/css/auramarket.css',
        'marketplace/static/src/js/live_webrtc.js',
       ],
    },

    'demo': [
        'demo/demo.xml',
    ],

    'application': True,

    'images': ['static/src/img/favicon.ico'],
}
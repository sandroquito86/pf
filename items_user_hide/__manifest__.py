# -*- coding: utf-8 -*-
{
    'name': "Menus del Usuario",

    'summary': "Oculta los items no necesarios del menu del usuario",

    'description': """
Oculta los items no necesarios del menu del usuario
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.5',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [],
    # only loaded in demonstration mode
    'demo': [
    ],
    'assets': {
        'web.assets_backend': [
            'items_user_hide/static/src/js/menu_items_hide_user.js',
        ],
},
}


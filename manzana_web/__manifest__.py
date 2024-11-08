# -*- coding: utf-8 -*-
{
    'name': "manzana_cuidados_formularios_web",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.5',

    # any module necessary for this one to work correctly
    'depends': ['base','website'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'data/menu_data.xml',
        'views/website_templates_forms.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'assets': {
        'web.assets_frontend': [
            #'manzana_elearning/static/src/js/button_file.js',
            'manzana_web/static/src/js/beneficiary_form_widget.js',
        ],
        'web.assets_backend': [
            #'manzana_elearning/static/src/components/attendance_beneficiary/attendance_beneficiary.js',
            #'manzana_elearning/static/src/components/attendance_beneficiary/attendance_beneficiary.xml',
        ],
},
}


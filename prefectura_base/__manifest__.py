# -*- coding: utf-8 -*-
{
    'name': "prefectura_base",

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
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr','base','mail','ps_m2m_field_attachment_preview','crnd_web_field_domain'],

    # always loaded
    'data': [
        'security/pf_security.xml',
        'security/ir.model.access.csv',
        'data/departmentos_job_data.xml',
        'data/data_base.xml',
        'data/ciudad_data.xml',
        'data/data_sucursal.xml',
        'data/data_programas.xml',
        'data/cie10_data.xml',
        'data/personal_data.xml',
        'views/pf_menu_view.xml',
        'views/pf_catalogo_items_views.xml',
        'views/pf_catalogo_views.xml',
        'views/pf_categoria_beneficiario_view.xml',
        'views/pf_beneficiarios_view.xml',
        'views/pf_sucursal_views.xml',
        'views/views_empleado/pf_empleado_view.xml',

        'views/views_empleado/pf_inactivar_employee_view.xml',
    ],
    'post_load': 'environment_extend',
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}


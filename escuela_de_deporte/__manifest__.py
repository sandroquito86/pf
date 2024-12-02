# -*- coding: utf-8 -*-
{
    'name': "escuela_de_deporte",

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
    'depends': ['base','hr','mail','prefectura_base', 'manzana_de_cuidados'],

    # always loaded
    'data': [

        'security/gi_security.xml',
        'security/ir.model.access.csv',
        # 'views/gi_beneficiarios_menu_view.xml',
        #CONFIGURACION        
        # CATALOGO
        # 'views/configuracion/catalogo/gi_catalogo_area_view.xml',
        # PLANIFICACIÓN
        
        #REGISTRO  
        # 'views/registro/gi_programa_view.xml',
          
        # 'views/registro/gi_solicitud_beneficiario_view.xml',   
          
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}


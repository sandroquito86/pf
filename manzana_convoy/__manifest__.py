# -*- coding: utf-8 -*-
{
    'name': "pf/manzana_convoy",

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
    'depends': ['base','mail','prefectura_base','manzana_de_cuidados'],

    # always loaded
    'data': [
        'security/mz_convoy_security.xml',
        'security/ir.model.access.csv',        
        # DATA
        'data/convoy_rule.xml',
        'data/data_mz_convoy_catalogo.xml',  
        'data/data_mz_convoy_instituciones_data.xml', 
        'data/convoy_finalizar_ir_cron.xml', 
        # MENU
        'views/menu/convoy_menu.xml', 
        # CONFIGURACION       
        'views/configuracion/pf_catalogo_views.xml',
        'views/configuracion/pf_catalogo_items_views.xml',
        # 'views/configuracion/mz_servicio_view.xml',
        # 'views/configuracion/mz_sub_servicios_view.xml',

        # PLANIFICACION
        'views/planificacion/mz_asignacion_servicio_view.xml',
         'views/planificacion/mz_planificacion_servicio_view.xml',

        # WIZARD
        'views/wizard/mz_convoy_beneficiario_wizard_view.xml', 
        'views/wizard/mz_convoy_dependiente_wizard_view.xml', 
        
        # REGISTRO
        'views/registro/mz_convoy_colaborador_view.xml',        
        'views/registro/mz_convoy_beneficiario_view.xml',                 
        'views/registro/mz_convoy_programas_view.xml',        
        'views/registro/mz_convoy_agendar_servicio_view.xml', 

        #EJECUCION
        'views/ejecucion/mz_agendar_servicio_view.xml', 
        
        
        # 'views/registro/convoy_view.xml',   
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}


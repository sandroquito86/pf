# -*- coding: utf-8 -*-
{
    'name': "Equipos Prefectura",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'GPL-3',

    # any module necessary for this one to work correctly
    #'depends': ['base','asset','th_gestion_hr'],
    'depends': ['base','web','mail','crnd_web_field_domain','hr','manzana_de_cuidados'],    
    'demo': [],

    # always loaded
    'data': [   
        'data/pg_equipo_marca_data.xml',
        'data/pg_equipo_modelo_data.xml', 
        'data/pg_equipo_categorizacion_grupo_data.xml', 
        'data/pg_equipo_categorizacion_categoria_data.xml', 
        'data/pg_equipo_categorizacion_nom_equipo_data.xml', 
       'data/pg_equipo_catalogo_caracteristica.xml',  
       'data/pg_equipo_conf_caracteristica.xml',   
        
        
    # #security
        'security/security_grupos.xml',
        'security/security_equipos_generales.xml',
        'security/ir.model.access.csv',          
       
    # #vistas        
        'views/pg_equipos_menu_view.xml',
        
    # #seguridad      
    #     # 'views/seguridad/asset_perfiles_view.xml',  
    #     'views/seguridad/asset_permiso_acceso_view.xml', 
    #     'views/seguridad/asset_seguridad_grupos.xml', 
    #     'views/seguridad/asset_perfiles_view.xml', 
                
    # vistas configuración    
        'views/configuracion/pg_equipos_marca_view.xml',
        'views/configuracion/pg_equipos_modelo_view.xml', 
        'views/configuracion/pg_equipos_grupo_view.xml',     
        'views/configuracion/pg_equipos_categoria_view.xml', 
        'views/configuracion/pg_equipos_nombre_equipo_view.xml',  
   
    # vista caracteristica
        'views/caracteristica/pg_equipos_catalogo_caracteristica_view.xml',   
        'views/caracteristica/pg_equipos_configuracion_caracteristica_view.xml',
  
                     
    # # vistas de activos               
        'views/equipos/pg_equipos_equipos_view.xml',   
    #     'views/board_views.xml',    


              
    ],
    'assets': {
        'web.assets_backend': [          
        ]
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],    
     'application': True,
}


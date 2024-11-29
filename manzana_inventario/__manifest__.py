# -*- coding: utf-8 -*-
{
    'name': "prefectura/manzana_inventario",

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
    'depends': ['base','prefectura_inventario'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/menu/mz_menu.xml',   
        #GESTION DE ALMACEN
        'views/conf_gestion_almacen/stock_almacen_view.xml',      
        'views/conf_gestion_almacen/stock_ubicaciones_view.xml',       
        'views/conf_gestion_almacen/stock_tipo_operacion_view.xml',     
        #TRASLADOS
        'views/traslados/mz_stock_operacion.xml',      
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}


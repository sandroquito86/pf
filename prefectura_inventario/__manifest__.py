# -*- coding: utf-8 -*-
{
    'name': "prefectura/prefectura_inventario",

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
    'depends': ['base','product','stock','prefectura_base','manzana_de_cuidados'],

    # always loaded
    'data': [
        'data/stock_grupos.xml',      
        'security/ir.model.access.csv', 
        'views/stock_menu_view.xml',
        #DATA         
        'data/pf_inventario_catalogo_data.xml',   

        
        #INVENTARIO
        'views/conf_gestion_almacen/stock_almacen_view.xml',
        'views/conf_gestion_almacen/stock_ubicaciones_view.xml',
        'views/conf_gestion_almacen/stock_tipo_operacion_view.xml',
        #REPORTE
        'views/reporte/stock_reporte_programa_view.xml',

        # 'views/inventario/pf_inventario_catalogo_views.xml',  
        # 'views/inventario/pf_inventario_items_views.xml',

        'views/stock/stock_product_view.xml', 
        # # WIZARD 
        # 'wizard/product_reabastecer_view.xml',   
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}


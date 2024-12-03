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
    'depends': ['base','product','stock','manzana_de_cuidados'],

    # always loaded
    'data': [
        # 'data/stock_grupos.xml',      
        'security/ir.model.access.csv', 
        'views/prefectura/prefectura_stock_menu_view.xml',
        'views/prefectura/prefectura_stock_categoria_producto_view.xml', 
        'views/prefectura/prefectura_stock_cantidad_view.xml', 
        'views/prefectura/prefectura_stock_almacen_view.xml',
        'views/prefectura/prefectura_stock_ubicacion_view.xml',
        'views/prefectura/prefectura_stock_tipo_operacion_view.xml',
        'views/prefectura/prefectura_stock_operacion_view.xml',
        'views/prefectura/prefectura_stock_producto_view.xml',
        'views/prefectura/prefectura_stock_lote_view.xml',

        # MANZANA
        'views/manzana/mz_menu.xml', 
         'views/manzana/manzana_stock_almacen_view.xml', 
         'views/manzana/manzana_stock_ubicacion_view.xml', 
         'views/manzana/manzana_stock_tipo_operacion_view.xml', 
         'views/manzana/manzana_stock_operacion_view.xml',  
        'views/manzana/mz_stock_cantidad_view.xml',   
         


        
        # #DATA         
        # 'data/pf_inventario_catalogo_data.xml',   

        
        # #INVENTARIO
        # 'views/prefectura/conf_gestion_almacen/stock_almacen_view.xml',
        # 'views/prefectura/conf_gestion_almacen/stock_ubicaciones_view.xml',
        # 'views/prefectura/conf_gestion_almacen/stock_tipo_operacion_view.xml',
      
        # # 'views/prefectura/inventario/pf_inventario_catalogo_views.xml',  
        # # 'views/prefectura/inventario/pf_inventario_items_views.xml',

        #'views/prefecturastock/stock_product_view.xml', 
        # # # WIZARD 
        # # 'wizard/product_reabastecer_view.xml',   
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}


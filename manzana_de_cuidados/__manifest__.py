# -*- coding: utf-8 -*-
{
    'name': "manzana_de_cuidados",

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
    'depends': ['hr','base', 'resource', 'mail','stock','prefectura_base','website_slides'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/mz_security.xml',
        'security/ir.model.access.csv',
        'data/data_catalogo.xml',
        'data/data_beneficiario.xml',
        'data/data_servicios.xml',
        'data/data_asig_servicios.xml',

        
        'menu/mz_menu.xml',
        'views/mz_catalogo_views.xml',
        'views/mz_catalogo_items_views.xml',
        'views/mz_programas_view.xml',
        'views/wizard/mz_convoy_control_asistencia.xml',        

        
        'views/views_servicio/mz_servicio_view.xml',
        'views/views_servicio/mz_sub_servicios_view.xml',
        
        'views/views_servicio/mz_wizard_agregar_turnos_extras.xml',
        'views/views_servicio/mz_asignacion_servicio_view.xml',
        'views/views_servicio/mz_horarios_servicio_view.xml',
        'views/views_servicio/mz_planificacion_servicio_view.xml',

        'views/views_beneficiario/mz_solicitud_beneficiario_view.xml',
        'views/views_beneficiario/mz_beneficiario_views.xml',
        
        'views/views_ejecucion/mz_wizard_reasignar_solicitud_turno_view.xml',
        'views/views_ejecucion/mz_agendar_servicio_view.xml',
        'views/views_ejecucion/mz_reagendar_servicio_view.xml',
        'views/views_ejecucion/mz_consulta_view.xml',
        'views/views_ejecucion/mz_consulta_psicologica_view.xml',
        'views/views_ejecucion/mz_cuidado_child_view.xml',
        'views/views_ejecucion/mz_asesoria_legal_view.xml',
        'views/views_ejecucion/mz_servicio_veterinario_view.xml',
        'views/views_ejecucion/mz_asistencia_servicio_view.xml',
        'views/views_ejecucion/mz_historia_clinica_view.xml',
        'views/views_ejecucion/mz_historia_clinica_psicologica_view.xml',
        
        
        'views/views_employee/mz_empleado_view.xml',
        'views/views_employee/mz_colaborador_view.xml',

        'views/views_for_beneficiario/mz_asistencia_servicio_benef_view.xml',
        
        
        'views/wizard/mz_wizard_quitar_publicacion_programa.xml',
        'views/views_servicio/mz_wizard_replanificar_turnos_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'manzana_de_cuidados/static/src/js/widget_fecha.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    

     'installable': True,
    'application': True,
    'auto_install': False,
}


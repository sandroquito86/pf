# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta
from random import randint
from datetime import datetime
from odoo.exceptions import UserError
import pytz
from datetime import timedelta
from babel.dates import format_date

class ConsultaPsicologica(models.Model):
    _name = 'mz.consulta.psicologica'
    _description = 'Consulta Psicológica'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'codigo'
    _order = 'fecha desc, hora desc'

    codigo = fields.Char(string='Código', readonly=True, store=True)
    fecha = fields.Date(string='Fecha', required=True, tracking=True)
    hora = fields.Float(string='Hora', required=True, tracking=True, compute='_compute_hora', store=True)
    beneficiario_id = fields.Many2one(string='Beneficiario', comodel_name='mz.beneficiario', ondelete='restrict', tracking=True, required=True)
    programa_id = fields.Many2one('pf.programas', string='Programa', required=True, default=lambda self: self.env.programa_id)
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.asignacion.servicio', ondelete='restrict', domain="[('programa_id', '=?', programa_id)]")
    personal_id = fields.Many2one(string='Personal Psicológico', comodel_name='hr.employee', ondelete='restrict', tracking=True)
    asistencia_servicio_id = fields.Many2one('mz.asistencia.servicio', string='Asistencia Servicio')
    genero_id = fields.Many2one('pf.items', string='Género', domain="[('catalogo_id', '=', ref('prefectura_base.genero'))]")
    fecha_nacimiento = fields.Date(string='Fecha de Nacimiento')
    # Campos específicos para consulta psicológica
    motivo_consulta = fields.Text(string='Motivo de Consulta', required=True, tracking=True)
    estado_emocional = fields.Text(string='Estado Emocional Actual', tracking=True)
    antecedentes_relevantes = fields.Text(string='Antecedentes Relevantes', tracking=True)
    evaluacion_inicial = fields.Text(string='Evaluación Inicial', tracking=True)
    plan_intervencion = fields.Text(string='Plan de Intervención', tracking=True)
    observaciones = fields.Text(string='Observaciones', tracking=True)
    # seguimiento 
    proxima_cita = fields.Date(string='Próxima Cita', tracking=True)
    horario_id_domain = fields.Char(compute="_compute_horario_id_domain", readonly=True, store=False, )
    horario_id = fields.Many2one(string='Turno', comodel_name='mz.planificacion.servicio', ondelete='restrict') 
    dias_disponibles_html = fields.Html(    string='Días Disponibles',    compute='_compute_dias_disponibles_html',    sanitize=False)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('final', 'Finalizado')
    ], string='Estado', default='draft', tracking=True)

    tipo_paciente = fields.Selection([
        ('titular', 'Titular'),
        ('dependiente', 'Dependiente')
    ], string='Tipo de Paciente', default='titular', required=True, tracking=True)
    
    dependiente_id = fields.Many2one(
        'mz.dependiente',
        string='Dependiente',
        tracking=True,
        domain="[('beneficiario_id', '=', beneficiario_id)]"
    )

    historia_psicologica_id = fields.Many2one(
        'mz.historia.psicologica', 
        string='Historia Psicológica', 
        readonly=True,
        store=True
    )

    diagnostico_ids = fields.One2many(
        'mz.diagnostico.psicologico.linea',
        'consulta_id',
        string='Diagnósticos'
    )
    historial_count = fields.Integer(
        string='Cantidad de Historias',
        compute='_compute_historial_count'
    )

    estado_new_solicitud = fields.Selection([
    ('borrador', 'Borrador'),
    ('solicitado', 'Solicitado')], string='Estado Solicitud', default='borrador', tracking=True)

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'El código de la consulta debe ser único.')
    ]

    @api.depends('fecha')
    def _compute_hora(self):
        for record in self:
            user_tz = self.env.user.tz or 'UTC'  # Obtiene la zona horaria del usuario o usa 'UTC' por defecto
            local_tz = pytz.timezone(user_tz)
            ahora = datetime.now(pytz.utc).astimezone(local_tz)  # Convierte la hora actual a la zona horaria del usuario
            record.hora = ahora.hour + ahora.minute / 60.0
            

    @api.depends('beneficiario_id', 'dependiente_id', 'tipo_paciente')
    def _compute_historial_count(self):
        for record in self:
            if record.tipo_paciente == 'titular':
                record.historial_count = len(record.beneficiario_id.historia_psicologica_ids)
            elif record.tipo_paciente == 'dependiente' and record.dependiente_id:
                record.historial_count = len(record.dependiente_id.historia_psicologica_ids)
            else:
                record.historial_count = 0

    @api.depends('servicio_id', 'personal_id','proxima_cita')
    def _compute_horario_id_domain(self):
        for record in self:
            if record.servicio_id and record.personal_id and record.proxima_cita:
                domain = ['|',  # OR operator
                                # Primera condición
                                '&', '&', '&',  # AND operators para la primera condición
                                    ('generar_horario_id.servicio_id', '=', record.servicio_id.id),
                                    ('generar_horario_id.personal_id', '=', record.personal_id.id),
                                    ('fecha', '=', record.proxima_cita),
                                    ('estado', '=', 'activo'),
                                # Segunda condición
                                '&', '&', '&', '&',  # AND operators para la segunda condición
                                    ('generar_horario_id.servicio_id', '=', record.servicio_id.id),
                                    ('generar_horario_id.personal_id', '=', record.personal_id.id),
                                    ('fecha', '=', record.proxima_cita),
                                    ('estado', '=', 'asignado'),
                                    ('estado_maximo_cont', '=', 'abierto')
                            ]
                horarios_planificados = self.env['mz.planificacion.servicio'].search(domain)
                
                horarios_disponibles = horarios_planificados.filtered(
                    lambda h: h.beneficiarios_count < h.maximo_beneficiarios
                )
                
                record.horario_id_domain = [('id', 'in', horarios_disponibles.ids)]
            else:
                record.horario_id_domain = [('id', 'in', [])]

    def _get_nombre_dia_espanol(self, fecha):
        # Diccionario de traducción de días
        dias = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes',
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        # Obtener el nombre del día en inglés y traducirlo
        nombre_dia_ingles = format_date(fecha, format='EEEE', locale='en')
        return dias.get(nombre_dia_ingles, nombre_dia_ingles)
    


    @api.depends('servicio_id', 'personal_id')
    def _compute_dias_disponibles_html(self):
        for record in self:
            if record.servicio_id and record.personal_id:
                fecha_inicio = datetime.now().date()
                fecha_fin = fecha_inicio + timedelta(days=30)
                
                domain = [
                            '|',  # Operador OR
                            # Primera condición
                            '&', '&', '&', '&', # Agrupa las condiciones de esta parte
                            ('generar_horario_id.servicio_id', '=', record.servicio_id.id),
                            ('generar_horario_id.personal_id', '=', record.personal_id.id),
                            ('fecha', '>=', fecha_inicio),
                            ('fecha', '<=', fecha_fin),
                            ('estado', '=', 'activo'),
                            # Segunda condición
                            '&', '&', '&', '&', '&',
                            ('generar_horario_id.servicio_id', '=', record.servicio_id.id),
                            ('generar_horario_id.personal_id', '=', record.personal_id.id),
                            ('fecha', '>=', fecha_inicio),
                            ('fecha', '<=', fecha_fin),
                            ('estado', '=', 'asignado'),
                            ('estado_maximo_cont', '=', 'abierto'),
                        ]
                
                horarios_planificados = self.env['mz.planificacion.servicio'].search(domain)
                horarios_disponibles = horarios_planificados.filtered(
                    lambda h: h.beneficiarios_count < h.maximo_beneficiarios
                )
                
                fechas_disponibles = set(h.fecha for h in horarios_disponibles)
                
                if fechas_disponibles:
                    # Calculamos cuántas columnas necesitamos (3 fechas por columna)
                    num_fechas = len(fechas_disponibles)
                    fechas_por_columna = 3
                    num_columnas = min(4, (num_fechas + fechas_por_columna - 1) // fechas_por_columna)
                    
                    html = '''
                    <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
                        <h4 style="color: #2c3e50; margin-bottom: 10px;">Días con turnos disponibles:</h4>
                        <div style="display: grid; grid-template-columns: repeat(''' + str(num_columnas) + ''', 1fr); gap: 10px;">
                    '''
                    
                    fechas_ordenadas = sorted(fechas_disponibles)
                    for fecha in fechas_ordenadas:
                        nombre_dia = self._get_nombre_dia_espanol(fecha)
                        html += f'''
                            <div style="background-color: #3498db; color: white; padding: 8px; 
                                      border-radius: 4px; text-align: center; margin-bottom: 5px;">
                                <div style="font-weight: bold;">{fecha.strftime('%d/%m/%Y')}</div>
                                <div style="font-size: 0.9em;">{nombre_dia}</div>
                            </div>
                        '''
                    
                    html += '</div></div>'
                    record.dias_disponibles_html = html
                else:
                    record.dias_disponibles_html = '''
                        <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; color: #856404;">
                            No hay turnos disponibles en los próximos 30 días
                        </div>
                    '''
            else:
                record.dias_disponibles_html = '''
                    <div style="background-color: #e2e3e5; padding: 10px; border-radius: 5px; color: #383d41;">
                        Seleccione un servicio y personal para ver días disponibles
                    </div>
                '''

    @api.model
    def default_get(self, fields_list):
        defaults = super(ConsultaPsicologica, self).default_get(fields_list)
        
        context = self.env.context
        defaults['personal_id'] = context.get('default_personal_id')
        defaults['beneficiario_id'] = context.get('default_beneficiario_id')
        defaults['tipo_paciente'] = context.get('default_tipo_paciente')
        defaults['dependiente_id'] = context.get('default_dependiente_id')
        defaults['servicio_id'] = context.get('default_servicio_id')
        defaults['programa_id'] = context.get('default_programa_id')
        defaults['fecha'] = context.get('default_fecha')
        if defaults.get('tipo_paciente'):
            if defaults['tipo_paciente'] == 'titular':
                if defaults.get('beneficiario_id'):
                    beneficiario = self.env['mz.beneficiario'].browse(defaults['beneficiario_id'])
                    defaults['genero_id'] = beneficiario.genero_id
                    defaults['fecha_nacimiento'] = beneficiario.fecha_nacimiento
            else:
                if defaults.get('dependiente_id'):
                    dependiente = self.env['mz.dependiente'].browse(defaults['dependiente_id'])
                    defaults['genero_id'] = dependiente.genero_id
                    defaults['fecha_nacimiento'] = dependiente.fecha_nacimiento    
        return defaults


    def action_view_historial(self):
        self.ensure_one()
        if self.tipo_paciente == 'titular':
            domain = [('beneficiario_id', '=', self.beneficiario_id.id)]
            name = f'Historial Clínico - {self.beneficiario_id.name}'
            context = {
                'default_beneficiario_id': self.beneficiario_id.id,
                'search_default_beneficiario_id': self.beneficiario_id.id,
            }
        else:
            domain = [('dependiente_id', '=', self.dependiente_id.id)]
            name = f'Historial Clínico - {self.dependiente_id.name}'
            context = {
                'default_dependiente_id': self.dependiente_id.id,
                'search_default_dependiente_id': self.dependiente_id.id,
            }
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'mz.historia.psicologica',
            'view_mode': 'tree,form',
            'domain':  domain,
            'context': context,
            'target': 'current',
        }
    
    def _generate_codigo(self):
        current_year = datetime.now().year
        current_month = datetime.now().month
        prefix = self.env.ref('prefectura_base.codigo_prefectura_items').name
        
        # Buscar el último código generado este año, excluyendo los registros en estado borrador
        last_record = self.env['mz.agendar_servicio'].search([
            ('create_date', '>=', f'{current_year}-01-01 00:00:00'),
            ('state', '!=', 'borrador'),
            ('programa_id', '=', self.programa_id.id),
        ], order='create_date desc', limit=1)
        if last_record and last_record.codigo and last_record.codigo_int:
            last_number = last_record.codigo_int
        else:
            last_number = 0

        new_number = last_number + 1
        # asigna valor al codigo_int del nuevo registro
        codigo_int = new_number
        new_number_str = str(new_number).zfill(7)
        # quiero retornar el codigo_int 2 valores
        return codigo_int, f'{prefix}-{self.programa_id.sigla}-{new_number_str}-{current_month:02d}-{current_year}'
    

    def solicitar_horario(self):
        """
        Método que se ejecuta al hacer clic en el botón 'Solicitar'.
        Crea un registro en mz.agendar_servicio y ejecuta la creación de asistencia.
        """
        if not self.horario_id:
                raise UserError("Debe seleccionar un horario.")
        if self.estado_new_solicitud == 'solicitado':
            raise UserError("Ya se ha solicitado el Turno.")
        codigo_int, codigo = self._generate_codigo()
        self.ensure_one()
        
        # Crear el registro en mz.agendar_servicio
        agendar_servicio_obj = self.env['mz.agendar_servicio']
        
        # Preparar los valores para el nuevo registro
        vals = {
            'beneficiario_id': self.beneficiario_id.id,
            'programa_id': self.programa_id.id,
            'servicio_id': self.servicio_id.id,
            'personal_id': self.personal_id.id,
            'fecha_solicitud': self.fecha,
            'horario_id': self.horario_id.id,
            'codigo': codigo,
            'codigo_int': codigo_int,
            'state': 'borrador',  # Estado inicial
            'tipo_beneficiario': self.tipo_paciente,
            'dependiente_id': self.dependiente_id.id if self.dependiente_id else False,
        }
        
        # Crear el nuevo registro
        nuevo_agendamiento = agendar_servicio_obj.create(vals)
        
        # Llamar al método para solicitar el horario en el nuevo registro
        try:
            resultado = nuevo_agendamiento.solicitar_horario()
            
            # Si la creación fue exitosa, actualizar el registro de consulta
            if resultado:
                nuevo_agendamiento.write({'state': 'solicitud'})
                self.estado_new_solicitud = 'solicitado'
                
                # Mostrar mensaje de éxito
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Éxito',
                        'message': 'Se ha creado el agendamiento y la asistencia correctamente',
                        'type': 'success',
                        'sticky': False,
                    }
                }
        except Exception as e:
            # En caso de error, mostrar mensaje y hacer rollback
            self.env.cr.rollback()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Error al crear el agendamiento: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
        
    def crear_historia_psicologica(self):
        for consulta in self:
            

            # Preparamos los datos iniciales para crear el registro
            valores_historia = {
                'tipo_paciente': consulta.tipo_paciente,
                'consulta_id': consulta.id,
                'personal_id': consulta.personal_id.id,
                'fecha': consulta.fecha,
                'motivo_consulta': consulta.motivo_consulta,
                'observaciones': consulta.observaciones,
                'estado_emocional': consulta.estado_emocional,
                'antecedentes_relevantes': consulta.antecedentes_relevantes,
                'evaluacion_inicial': consulta.evaluacion_inicial,
                'plan_intervencion': consulta.plan_intervencion,
                'beneficiario_id': consulta.beneficiario_id.id if consulta.tipo_paciente == 'titular' else False,
                'dependiente_id': consulta.dependiente_id.id if consulta.tipo_paciente != 'titular' else False,
            }

            # Creamos la historia clínica
            historia_psicologica= self.env['mz.historia.psicologica'].create(valores_historia)

            consulta.historia_psicologica_id = historia_psicologica.id
            for diagnostico in consulta.diagnostico_ids:
                diagnostico.write({'historia_psicologica_id': historia_psicologica.id})

    def actualizar_historia_psicologica(self):
        for consulta in self:
            if consulta.historia_psicologica_id:
                consulta.historia_psicologica_id.write({
                    'motivo_consulta': consulta.motivo_consulta,
                    'observaciones': consulta.observaciones,
                    'estado_emocional': consulta.estado_emocional,
                    'antecedentes_relevantes': consulta.antecedentes_relevantes,
                    'evaluacion_inicial': consulta.evaluacion_inicial,
                    'plan_intervencion': consulta.plan_intervencion,                   
                    
                })


    def create(self, vals):
        consulta = super(ConsultaPsicologica, self).create(vals)
        consulta.crear_historia_psicologica()
        self.env['mz.asistencia_servicio'].search([('codigo', '=', vals['codigo'])]).write({'atendido': True, 'consulta_psicologica_id': consulta.id})
        return consulta
    
    def write(self, vals):
        res = super(ConsultaPsicologica, self).write(vals)
        self.actualizar_historia_psicologica()
        return res
    
    def action_finalizar(self):
        self.state = 'final'

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar turnos cuando viene el contexto
        """
        args = args or []
        user = self.env.user
        
        # Evitar recursión usando un contexto especial
        if not self._context.get('disable_custom_search'):
            if self._context.get('filtrar_programa'):                   
                # Verificar grupos
                if user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
                    # Para coordinador: ver solo programas de módulo 2
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id.modulo_id', '=', 2)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                elif user.has_group('manzana_de_cuidados.group_mz_registro_informacion') or \
                    user.has_group('manzana_de_cuidados.group_coordinador_manzana') or \
                    user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id', '=', user.programa_id.id),
                        ('state', '=', 'final')
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                elif user.has_group('manzana_de_cuidados.group_mz_prestador_servicio'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    if_medico = False
                    for servicio in user.employee_id.servicios_ids:
                        if servicio.servicio_id.if_consulta_psicologica:
                            if_medico = True
                            break
                    if if_medico:
                        programa_ids = self.with_context(disable_custom_search=True).search([
                                    '|',
                                        '&',
                                            ('programa_id', '=', user.programa_id.id),
                                            ('state', '=', 'final'),
                                        ('personal_id', '=', user.employee_id.id)
                                    ]).ids
                        base_args = [('id', 'in', programa_ids)]
                    else:
                        base_args = [('id', 'in', [])]
                else :
                    # Para usuarios sin rol especial: ver solo sus propios programas
                    base_args = [('id', 'in', [])]

                args = base_args + args

        return super(ConsultaPsicologica, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
    
    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user
        if user.has_group('manzana_de_cuidados.group_mz_prestador_servicio') or \
            user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_consulta_psicologica_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_consulta_psicologica_form').id
        else:
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_consulta_psicologica_tree_limit').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_consulta_psicologica_form_limit').id


        return super().get_view(
            view_id=view_id, 
            view_type=view_type, 
            context=context, 
            toolbar=toolbar, 
            submenu=submenu,
            **kwargs
        )
    

    # def get_appropriate_view(self):
    #     # Obtener el usuario actual
    #     user = self.env.user
        
    #     # Definir vistas por defecto (limitadas)
    #     tree_view = self.env.ref('manzana_de_cuidados.view_mz_consulta_psicologica_tree_limit').id
    #     form_view = self.env.ref('manzana_de_cuidados.view_mz_consulta_psicologica_form_limit').id
        
    #     # Verificar si el usuario tiene permisos específicos
    #     if (user.has_group('manzana_de_cuidados.group_mz_prestador_servicio') or \
    #         user.has_group('manzana_de_cuidados.group_beneficiario_manager')):
    #         # Vistas completas para usuarios con permisos
    #         tree_view = self.env.ref('manzana_de_cuidados.view_mz_consulta_psicologica_tree').id
    #         form_view = self.env.ref('manzana_de_cuidados.view_mz_consulta_psicologica_form_read').id
        
    #     # Preparar la acción de ventana
    #     action = {
    #         'name': 'Consulta Psicológicas',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'mz.consulta.psicologica',
    #         'view_mode': 'tree,form',
    #         'views': [
    #             (tree_view, 'tree'),
    #             (form_view, 'form')
    #         ],
    #         'context': {
    #             'default_modulo_id': 2,
    #             'filtrar_programa': True
    #         },
    #         'target': 'current'
    #     }
        
    #     return action

class DiagnosticoPsicologicoLinea(models.Model):
    _name = 'mz.diagnostico.psicologico.linea'
    _description = 'Línea de Diagnóstico Psicológico'

    consulta_id = fields.Many2one('mz.consulta.psicologica', string='Consulta', required=True, ondelete='cascade')
    cie10_id = fields.Many2one('pf.cie10', string='Diagnóstico CIE-10', tracking=True)
    detalle = fields.Text(string='Detalle del diagnóstico')
    es_principal = fields.Boolean(string='Diagnóstico Principal', default=False)
    historia_psicologica_id = fields.Many2one('mz.historia.psicologica', string='Historia Psicológica', ondelete='cascade')

    @api.constrains('es_principal', 'consulta_id')
    def _check_diagnostico_principal(self):
        for record in self:
            if record.es_principal:
                # Verifica que no haya otro diagnóstico principal en la misma consulta
                otros_principales = self.search([
                    ('consulta_id', '=', record.consulta_id.id),
                    ('es_principal', '=', True),
                    ('id', '!=', record.id)
                ])
                if otros_principales:
                    raise UserError('Solo puede haber un diagnóstico principal por consulta.')
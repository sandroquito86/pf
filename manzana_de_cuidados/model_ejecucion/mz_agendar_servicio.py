# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from datetime import timedelta
from babel.dates import format_date


class AgendarServicio(models.Model):
    _name = 'mz.agendar_servicio'
    _description = 'Agendar Servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _rec_name = 'codigo'
    
    STATE_SELECTION = [('borrador', 'Borrador'), ('solicitud', 'Solicitado'),('por_reeplanificar', 'Por Reagendar'),
                       ('atendido', 'Atendido'), ('anulado', 'Anulado')]

    state = fields.Selection(STATE_SELECTION, 'Estado', readonly=True, tracking=True, default='borrador', )
    modulo_id = fields.Many2one(string='Módulo', comodel_name='pf.modulo', ondelete='restrict',
                                default=lambda self: self.env.ref('prefectura_base.modulo_2').id,tracking=True)
    beneficiario_id_domain = fields.Char(compute="_compute_beneficiario_id_domain", readonly=True, store=False, )
    beneficiario_id = fields.Many2one(string='Beneficiario', comodel_name='mz.beneficiario', ondelete='restrict', tracking=True, required=True)
    tipo_beneficiario = fields.Selection([('titular', 'Titular'),('dependiente', 'Dependiente')], string='Tipo de Beneficiario', default='titular', required=True, tracking=True)    
    dependiente_id = fields.Many2one('mz.dependiente',string='Dependiente',tracking=True,domain="[('beneficiario_id', '=', beneficiario_id)]" )
    mascota_id = fields.Many2one('mz.mascota', string='Mascota', ondelete='restrict', domain="[('beneficiario_id', '=', beneficiario_id),('estado', '=', 'activo')]")
    programa_id = fields.Many2one('pf.programas', string='Programa', required=True, default=lambda self: self.env.programa_id)
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.asignacion.servicio', ondelete='restrict',domain="[('programa_id', '=?', programa_id)]")  
    servicio_base_id = fields.Many2one(string='Servicios', comodel_name='mz.servicio', ondelete='restrict', related='servicio_id.servicio_id', store=True)
    # generar_horario_id
    personal_id_domain = fields.Char(compute="_compute_personal_id_domain", readonly=True, store=False, )
    personal_id = fields.Many2one(string='Personal', comodel_name='hr.employee', ondelete='restrict',)
    horario_id_domain = fields.Char(compute="_compute_horario_id_domain", readonly=True, store=False, )
    fecha_solicitud = fields.Date(string='Fecha', required=True, tracking=True)
    horario_id = fields.Many2one(string='Turno', comodel_name='mz.planificacion.servicio', ondelete='restrict')  
    codigo = fields.Char(string='Código', readonly=True, store=True)
    mensaje = fields.Text(string='Mensaje', compute='_compute_mensaje')
    active = fields.Boolean(default=True, string='Activo', tracking=True)
    if_sub_servicio = fields.Boolean(string='Sub Servicio', compute='_compute_if_sub_servicio')
    sub_servicio_id = fields.Many2one('mz.sub.servicio', string="Sub Servicio", ondelete='restrict')
    domain_sub_servicio_ids = fields.Char(string='Domain Sub servicios',compute='_compute_domain_sub_servicio_ids')
    if_admin = fields.Boolean(string='Es administrador', compute='_compute_if_administrador', default=False)
    dias_disponibles_html = fields.Html(    string='Días Disponibles',    compute='_compute_dias_disponibles_html',    sanitize=False)
    codigo_int = fields.Integer(string='Código', store=True)
    tipo_servicio = fields.Selection([('normal', 'Bienestar Personal'), ('medico', 'Salud'), ('cuidado_infantil', 'Cuidado Infantil'), ('mascota', 'Mascota'), ('asesoria_legal', 'Asesoria Legal')], string='Clasificación de Servicio', compute='_compute_tipo_servicio')

    @api.onchange('programa_id', 'servicio_id')
    def _onchange_modulo_id(self):
        for record in self:
            if record.programa_id:
                record.modulo_id = record.programa_id.modulo_id.id

    @api.depends('servicio_id')
    def _compute_tipo_servicio(self):
        for record in self:
            record.tipo_servicio = record.servicio_id.servicio_id.tipo_servicio
                
    
    @api.constrains('tipo_beneficiario', 'dependiente_id')
    def _check_dependiente(self):
        for record in self:
            if record.tipo_beneficiario == 'dependiente' and not record.dependiente_id:
                raise UserError('Debe seleccionar un dependiente cuando el tipo de beneficiario es "Dependiente"')

    @api.constrains('servicio_id')
    def _check_servicio_if_mascota(self):
        if self.servicio_id.servicio_id.tipo_servicio == 'mascota' and self.tipo_beneficiario == 'dependiente':
            raise UserError('No se puede seleccionar un dependiente para el servicio de mascota.')


    @api.depends('servicio_id')
    def _compute_domain_sub_servicio_ids(self):
        for record in self:
            if record.servicio_id:
                sub_servicios = self.env['mz.sub.servicio'].search([('id', 'in', self.servicio_id.sub_servicio_ids.ids)])
                record.domain_sub_servicio_ids = [('id', 'in', sub_servicios.ids)]
            else:
                record.domain_sub_servicio_ids = [('id', 'in', [])]
    
    @api.depends('servicio_id')
    def _compute_if_sub_servicio(self):
        for record in self:
            if record.servicio_id.sub_servicio_ids:
                record.if_sub_servicio = True
            else:
                record.if_sub_servicio = False

    @api.onchange('servicio_id')
    def _onchange_if_administrador(self):
        for record in self:
            record.if_admin = bool(self.env.ref('manzana_de_cuidados.group_beneficiario_manager') in self.env.user.groups_id)

   


    @api.depends('servicio_id')
    def _compute_if_administrador(self):
        for record in self:
            record.if_admin = bool(self.env.ref('manzana_de_cuidados.group_beneficiario_manager') in self.env.user.groups_id)
    

    @api.depends('servicio_id', 'personal_id')
    def _compute_mensaje(self):
        dia_dict = dict(self.env['mz.detalle.horarios'].fields_get(allfields=['dias'])['dias']['selection'])
        for record in self:
            if record.servicio_id and record.personal_id:
                domain = [
                    ('servicio_id', '=', record.servicio_id.id),
                    ('personal_id', '=', record.personal_id.id),
                    ('active', '=', True),
                ]
                horarios_planificados = self.env['mz.horarios.servicio'].search(domain)
                if horarios_planificados:
                    dias_nombres = [dia_dict.get(horario.dias, '') for horario in horarios_planificados.detalle_horario_ids]
                    record.mensaje = f'Horarios de {record.personal_id.name}: ' + ' - '.join(dias_nombres)
                else:
                    record.mensaje = 'No Tiene Horarios Asignados'
            else:
                record.mensaje = ''


    @api.constrains('beneficiario_id', 'horario_id')
    def _check_unique_beneficiario_horario(self):
        for record in self:
            existing = self.search([
                ('beneficiario_id', '=', record.beneficiario_id.id),
                ('horario_id', '=', record.horario_id.id),
                ('id', '!=', record.id)
            ])            
            if existing:
                raise UserError("El beneficiario ya ha solicitado este horario.")       
            
    @api.constrains('horario_id', 'beneficiario_id')
    def _check_horario_capacity(self):
        for record in self:
            if record.horario_id and record.beneficiario_id:
                # Contar las asistencias actuales para este horario
                asistencias_count = self.env['mz.asistencia_servicio'].search_count([
                    ('planificacion_id', '=', record.horario_id.id)
                ])
                
                # Verificar si se excede la capacidad máxima
                if asistencias_count >= record.horario_id.maximo_beneficiarios:
                    raise UserError(f"El turno seleccionado ya ha alcanzado su capacidad máxima de {record.horario_id.maximo_beneficiarios} beneficiarios.")

            
                
    @api.depends('modulo_id','programa_id')
    def _compute_beneficiario_id_domain(self):
      for record in self:         
        beneficiario_ids = record.beneficiario_id.search([('programa_id','=',record.programa_id.id)]).ids
        record.beneficiario_id_domain = [('id', 'in', beneficiario_ids)]    

    @api.depends('servicio_id')
    def _compute_personal_id_domain(self):
      for record in self:    
        personal = self.env['mz.horarios.servicio'].search([('servicio_id','=',record.servicio_id.id)]).personal_id.ids        
        record.personal_id_domain = [('id', 'in', personal)]     

    
    @api.depends('servicio_id', 'personal_id','fecha_solicitud')
    def _compute_horario_id_domain(self):
        for record in self:
            if record.servicio_id and record.personal_id and record.fecha_solicitud:
                domain = ['|',  # OR operator
                                # Primera condición
                                '&', '&', '&',  # AND operators para la primera condición
                                    ('generar_horario_id.servicio_id', '=', record.servicio_id.id),
                                    ('generar_horario_id.personal_id', '=', record.personal_id.id),
                                    ('fecha', '=', record.fecha_solicitud),
                                    ('estado', '=', 'activo'),
                                # Segunda condición
                                '&', '&', '&', '&',  # AND operators para la segunda condición
                                    ('generar_horario_id.servicio_id', '=', record.servicio_id.id),
                                    ('generar_horario_id.personal_id', '=', record.personal_id.id),
                                    ('fecha', '=', record.fecha_solicitud),
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


    @api.onchange('servicio_id')
    def _onchange_validar_servicio_if_dependiente(self):
      for record in self:    
        if record.servicio_id.servicio_id.tipo_servicio == 'cuidado_infantil' and record.tipo_beneficiario != 'dependiente':
            raise UserError("Este servicio es Exclusivamente para dependietes(Hija o Hijo).")
        if record.servicio_id.servicio_id.tipo_servicio == 'mascota':
            if record.tipo_beneficiario == 'dependiente':
                record.dependiente_id = False
                record.tipo_beneficiario = 'titular'
                record.servicio_id = False
            

    @api.onchange('programa_id')
    def _onchange_programa_id(self):
        for record in self:
            record.beneficiario_id = False
            record.servicio_id = False
            record.personal_id = False
            record.fecha_solicitud = False
            record.horario_id = False
            record.tipo_beneficiario = 'titular'
            self.dependiente_id = False
    
    @api.onchange('beneficiario_id')
    def _onchange_beneficiario_id(self):
        for record in self:
            record.servicio_id = False
            record.personal_id = False
            record.fecha_solicitud = False
            record.horario_id = False
            record.tipo_beneficiario = 'titular'
            self.dependiente_id = False

    @api.onchange('servicio_id')
    def _onchange_servicio_id(self):
        for record in self:
            record.personal_id = False
            record.fecha_solicitud = False
            record.horario_id = False

    @api.onchange('tipo_beneficiario')
    def _onchange_tipo_beneficiario(self):
        self.dependiente_id = False
        self.mascota_id = False


    @api.onchange('personal_id')
    def _onchange_personal_id(self):
        for record in self:
            record.fecha_solicitud = False
            record.horario_id = False
            if record.servicio_id and record.personal_id:
                domain = [
                    ('generar_horario_id.servicio_id', '=', record.servicio_id.id),
                    ('generar_horario_id.personal_id', '=', record.personal_id.id),
                    ('fecha', '>=', fields.Date.today()),
                    ('estado', '=', 'activo'),
                ]
                horarios_planificados = self.env['mz.planificacion.servicio'].search(domain)
                horarios_disponibles = horarios_planificados.filtered(
                    lambda h: h.beneficiarios_count < h.maximo_beneficiarios
                )
                if not horarios_disponibles:
                    raise UserError(f"No hay Turnos disponibles para el servicio de {record.servicio_id.servicio_id.name} con {record.personal_id.name}.")
            

    # def _generate_codigo(self):
    #     current_year = datetime.now().year
    #     current_month = datetime.now().month
    #     prefix = self.env.ref('prefectura_base.codigo_prefectura_items').name
        
    #     # Buscar el último código generado este año, excluyendo los registros en estado borrador
    #     last_record = self.search([
    #         ('create_date', '>=', f'{current_year}-01-01 00:00:00'),
    #         ('state', '!=', 'borrador'),
    #         ('programa_id', '=', self.programa_id.id),
    #     ], order='codigo_int desc', limit=1)
    #     if last_record and last_record.codigo and last_record.codigo_int:
    #         last_number = last_record.codigo_int
    #     else:
    #         last_number = 0

    #     new_number = last_number + 1
    #     # asigna valor al codigo_int del nuevo registro
    #     self.codigo_int = new_number
    #     new_number_str = str(new_number).zfill(7)
        
    #     return f'{prefix}-{self.programa_id.sigla}-{new_number_str}-{current_month:02d}-{current_year}'

    def _generate_codigo(self):
        prefix = self.env.ref('prefectura_base.codigo_prefectura_items').name
        
        # Si el registro es nuevo, primero guardamos para obtener el ID
        if not self.id:
            self._cr.execute('SAVEPOINT pregenerate_code')
            self.flush()
        
        # Usamos el ID del registro para el código
        codigo_numero = str(self.id).zfill(5)  # Convierte el ID a 5 dígitos
        
        # Generamos el código final
        codigo = f'{prefix}-{self.programa_id.sigla}-{codigo_numero}'
        
        
        return codigo

    # def aprobar_horario(self):
    #     for record in self:
    #         # Verificar nuevamente la capacidad antes de aprobar
    #         asistencias_count = self.env['mz.asistencia_servicio'].search_count([
    #             ('planificacion_id', '=', record.horario_id.id)
    #         ])
    #         if asistencias_count >= record.horario_id.maximo_beneficiarios:
    #             raise UserError(f"No se puede aprobar. El turno ya ha alcanzado su capacidad máxima de {record.horario_id.maximo_beneficiarios} beneficiarios.")
            
    #         record.state = 'aprobado'
    #         if record.horario_id and record.beneficiario_id:
    #             self.env['mz.asistencia_servicio'].create({
    #                 'planificacion_id': record.horario_id.id,
    #                 'beneficiario_id': record.beneficiario_id.id,
    #                 'codigo': record.codigo,
    #             })

    # quiero capturar el metodo create para validar que el beneficiario o el dependiente no tenga una solicitud pendiente en el mismo servicio
    @api.model
    def create(self, vals):
        if vals.get('tipo_beneficiario') == 'titular':
            servicio = self.env['mz.asignacion.servicio'].browse(vals.get('servicio_id'))
            if servicio.servicio_id.tipo_servicio == 'mascota':
                existe_asistencia = self.env['mz.asistencia_servicio'].search([
                    ('beneficiario_id', '=', vals.get('beneficiario_id')),
                    ('mascota_id', '=', vals.get('mascota_id')),
                    ('asistio', '=', 'pendiente'),
                    ('servicio_id', '=', vals.get('servicio_id'))
                ],limit=1)
                if existe_asistencia:
                    raise UserError(f'La macosta ya tiene una solicitud pendiente en {existe_asistencia.servicio_id.name} con {existe_asistencia.personal_id.name}. para la fecha {existe_asistencia.fecha}.')
            else:
                existe_asistencia = self.env['mz.asistencia_servicio'].search([
                    ('beneficiario_id', '=', vals.get('beneficiario_id')),
                    ('asistio', '=', 'pendiente'),
                    ('servicio_id', '=', vals.get('servicio_id'))
                ],limit=1)
                # if existe_asistencia:
                #     raise UserError(f'El beneficiario ya tiene una solicitud pendiente en {existe_asistencia.servicio_id.name} con {existe_asistencia.personal_id.name}. para la fecha {existe_asistencia.fecha}.')
        else:
            existe_asistencia = self.env['mz.asistencia_servicio'].search([
                ('beneficiario_id', '=', vals.get('beneficiario_id')),
                ('dependiente_id', '=', vals.get('dependiente_id')),
                ('asistio', '=', 'pendiente'),
                ('servicio_id', '=', vals.get('servicio_id'))
            ],limit=1)
            if existe_asistencia:
                raise UserError(f'El dependiente ya tiene una solicitud pendiente en {existe_asistencia.servicio_id.name} con {existe_asistencia.personal_id.name}. para la fecha {existe_asistencia.fecha}.')
        return super(AgendarServicio, self).create(vals)

    def solicitar_horario(self):
        for record in self:
            if not record.horario_id:
                raise UserError("Debe seleccionar un horario.")
            codigo = self._generate_codigo()
            record.codigo = codigo
            # Verificar nuevamente la capacidad antes de aprobar
            asistencias_count = self.env['mz.asistencia_servicio'].search_count([
                ('planificacion_id', '=', record.horario_id.id)
            ])
            if asistencias_count >= record.horario_id.maximo_beneficiarios:
                raise UserError(f"No se puede aprobar. El turno ya ha alcanzado su capacidad máxima de {record.horario_id.maximo_beneficiarios} beneficiarios.")
            if record.tipo_beneficiario == 'titular':
                servicio = record.servicio_id
                if servicio.servicio_id.tipo_servicio == 'mascota':
                    existe_asistencia = self.env['mz.asistencia_servicio'].search([
                        ('beneficiario_id', '=', record.beneficiario_id.id),
                        ('mascota_id', '=', record.mascota_id.id),
                        ('asistio', '=', 'pendiente'),
                        ('servicio_id', '=', record.servicio_id.id)
                    ],limit=1)
                    if existe_asistencia:
                        raise UserError(f'La macosta ya tiene una solicitud pendiente en {existe_asistencia.servicio_id.name} con {existe_asistencia.personal_id.name}. para la fecha {existe_asistencia.fecha}.')
                else:
                    existe_asistencia = self.env['mz.asistencia_servicio'].search([
                        ('beneficiario_id', '=', record.beneficiario_id.id),
                        ('asistio', '=', 'pendiente'),
                        ('servicio_id', '=', record.servicio_id.id)
                    ],limit=1)
                    # if existe_asistencia:
                    #     raise UserError(f'El beneficiario ya tiene una solicitud pendiente en {existe_asistencia.servicio_id.name} con {existe_asistencia.personal_id.name}. para la fecha {existe_asistencia.fecha}.')
            else:
                existe_asistencia = self.env['mz.asistencia_servicio'].search([
                    ('beneficiario_id', '=', record.beneficiario_id.id),
                    ('dependiente_id', '=', record.dependiente_id.id),
                    ('asistio', '=', 'pendiente'),
                    ('servicio_id', '=', record.servicio_id.id)
                ],limit=1)
                if existe_asistencia:
                    raise UserError(f'El dependiente ya tiene una solicitud pendiente en {existe_asistencia.servicio_id.name} con {existe_asistencia.personal_id.name}. para la fecha {existe_asistencia.fecha}.')
            record.state = 'solicitud'
            if record.horario_id and record.beneficiario_id:
                self.env['mz.asistencia_servicio'].create({
                    'planificacion_id': record.horario_id.id,
                    'beneficiario_id': record.beneficiario_id.id,
                    'fecha': record.fecha_solicitud,
                    'programa_id': record.programa_id.id,
                    'servicio_id': record.servicio_id.id,
                    'personal_id': record.personal_id.id,
                    'codigo': record.codigo,
                    'tipo_beneficiario': record.tipo_beneficiario,
                    'dependiente_id': record.dependiente_id.id if record.dependiente_id else False,
                    'mascota_id': record.mascota_id.id if record.mascota_id else False,
                })
            record.horario_id.write({
            'estado': 'asignado',
            'beneficiario_ids': [(4, record.beneficiario_id.id)],
            })
        return True

    @api.constrains('fecha_solicitud')
    def _check_date(self):
        for record in self:
            if record.fecha_solicitud < fields.Date.today():
                raise UserError("La fecha no puede ser anterior a la fecha actual.")

    @api.onchange('fecha_solicitud')
    def _onchange_fecha_valida_solicitud(self):
        self.horario_id = False
        fecha_actual = datetime.now() - timedelta(hours=5)
        if self.fecha_solicitud  and self.fecha_solicitud < fecha_actual.date():
            self.fecha_solicitud = fecha_actual.date()
            return {
                'warning': {
                    'title': "Fecha inválida",
                    'message': "La fecha ha sido ajustada a la fecha actual."
                }
            }

    def anular_horario(self):
        for record in self:
            raise UserError("No se puede anular la solicitud. Por favor, contacte al administrador del sistema.")
        
    def action_wizard_reasignar_solicitud(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reagendar nuevo Turno',
            'res_model': 'mz.wizard.reasignar.solicitud',
            'view_mode': 'form',
            'view_id': self.env.ref('manzana_de_cuidados.view_wizard_reasignar_solicitud_form').id,
            'target': 'new',
            'context': {
                'default_solicitud_id': self.id,
            },
        }

    def unlink(self):
        for record in self:
            if record.state != 'borrador':
                raise UserError("No se puede eliminar un registro que no esté en estado borrador.")
        return super(AgendarServicio, self).unlink()
    

    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user

        if user.has_group('manzana_de_cuidados.group_mz_registro_informacion') or \
        user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_agendar_servicio_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_agendar_servicio_form').id
        elif user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia') or \
             user.has_group('manzana_de_cuidados.group_mz_registro_informacion') or \
             user.has_group('manzana_de_cuidados.group_coordinador_manzana'):
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_agendar_servicio_tree_limit').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_agendar_servicio_form_limit').id

        return super().get_view(
            view_id=view_id, 
            view_type=view_type, 
            context=context, 
            toolbar=toolbar, 
            submenu=submenu,
            **kwargs
        )
    

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar turnos cuando viene el contexto
        """
        args = args or []
        user = self.env.user
        
        # Evitar recursión usando un contexto especial
        if not self._context.get('disable_custom_search'):
            if self._context.get('filtrar_turno'):                   
                # Verificar grupos
                if user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
                    # Para coordinador: ver solo programas de módulo 2
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id.modulo_id', '=', 2)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                elif user.has_group('manzana_de_cuidados.group_mz_registro_informacion'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id', '=', user.programa_id.id)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                elif user.has_group('manzana_de_cuidados.group_coordinador_manzana') or \
                    user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    programa_ids = self.with_context(disable_custom_search=True).search([
                                    '|', 
                                    '&', ('programa_id', '=', user.programa_id.id), ('state', '!=', 'borrador'),
                                    '&','&', ('programa_id', '=', user.programa_id.id), ('state', '=', 'borrador'), ('create_uid', '=', user.id)
                                ]).ids
                    base_args = [('id', 'in', programa_ids)]
                else :
                    # Para usuarios sin rol especial: ver solo sus propios programas
                    programa_ids = self.with_context(disable_custom_search=True).search([
                                    '|', 
                                    '&', ('personal_id', '=', user.employee_id.id), ('state', '!=', 'borrador'),
                                    '&','&', ('personal_id', '=', user.employee_id.id), ('state', '=', 'borrador'), ('create_uid', '=', user.id)
                                ]).ids
                    base_args = [('id', 'in', programa_ids)]

                args = base_args + args

        return super(AgendarServicio, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
    

class WizardReasignarSolicitud(models.TransientModel):
    _name = 'mz.wizard.reasignar.solicitud'
    _description = 'Wizard para Reagendar Solicitud/turno'

    solicitud_id = fields.Many2one('mz.agendar_servicio', string='Solicitud', required=True)
    nueva_fecha = fields.Date(string='Nueva Fecha', required=True)
    nuevo_horario_id = fields.Many2one('mz.planificacion.servicio', string='Nuevo Turno', required=True)
    horario_id_domain = fields.Char(compute="_compute_horario_id_domain", readonly=True, store=False, )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'solicitud_id' in fields_list and self.env.context.get('active_id'):
            res['solicitud_id'] = self.env.context['active_id']
        return res
    
    def action_reasignar(self):
        self.ensure_one()
        solicitud = self.solicitud_id
        solicitud.write({
            'fecha_solicitud': self.nueva_fecha,
            'horario_id': self.nuevo_horario_id.id,
            'state': 'solicitud',
        })
        solicitud.solicitar_horario()
        return {'type': 'ir.actions.act_window_close'}

    @api.depends('solicitud_id.servicio_id', 'solicitud_id.personal_id','nueva_fecha')
    def _compute_horario_id_domain(self):
        for record in self:
            if record.solicitud_id.servicio_id and record.solicitud_id.personal_id and record.nueva_fecha:
                domain = [
                            '|',  # Operador OR
                            # Primera condición
                            '&', '&', '&', # Agrupa las condiciones de esta parte
                            ('generar_horario_id.servicio_id', '=', record.solicitud_id.servicio_id.id),
                            ('generar_horario_id.personal_id', '=', record.solicitud_id.personal_id.id),
                            ('fecha', '=', record.nueva_fecha),
                            ('estado', '=', 'activo'),
                            # Segunda condición
                            '&', '&', '&', '&',
                            ('generar_horario_id.servicio_id', '=', record.solicitud_id.servicio_id.id),
                            ('generar_horario_id.personal_id', '=', record.solicitud_id.personal_id.id),
                            ('fecha', '=', record.nueva_fecha),
                            ('estado', '=', 'asignado'),
                            ('estado_maximo_cont', '=', 'abierto'),
                        ]
                horarios_planificados = self.env['mz.planificacion.servicio'].search(domain)
                
                horarios_disponibles = horarios_planificados.filtered(
                    lambda h: h.beneficiarios_count < h.maximo_beneficiarios
                )
                
                record.horario_id_domain = [('id', 'in', horarios_disponibles.ids)]
            else:
                record.horario_id_domain = [('id', 'in', [])]
       
       

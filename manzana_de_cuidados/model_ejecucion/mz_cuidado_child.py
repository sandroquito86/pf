# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class MzCuidadoChild(models.Model):
    _name = 'mz.cuidado.child'
    _description = 'Gestión de Servicios Infantiles'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, hora_entrada desc'
    _rec_name = 'codigo'

    # Campos de identificación y control
    codigo = fields.Char(string='Código', required=True,  store=True)

    tipo_servicio = fields.Selection([
        ('guarderia', 'Guardería'),
        ('lectura', 'Animación a la Lectura')
    ], string='Tipo de Servicio', required=True, tracking=True, default='guarderia')
    
    # Campos relacionales
    beneficiario_id = fields.Many2one(
        'mz.beneficiario',
        string='Beneficiario',
        required=True,
        tracking=True
    )
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.asignacion.servicio', ondelete='restrict')
    tipo_beneficiario = fields.Selection([('titular', 'Titular'),('dependiente', 'Dependiente') ], string='Tipo de Beneficiario')
    dependiente_id = fields.Many2one(
        'mz.dependiente',
        string='Niño/a',
        required=True,
        domain="[('beneficiario_id', '=', beneficiario_id)]",
        tracking=True
    )
    personal_id = fields.Many2one(
        'hr.employee',
        string='Prestador de Servicio',
        required=True,
        tracking=True
    )
    programa_id = fields.Many2one(
        'pf.programas',
        string='Programa',
        required=True
    )
    asistencia_servicio_id = fields.Many2one(
        'mz.asistencia_servicio',
        string='Asistencia Servicio'
    )

    # Campos de tiempo
    fecha = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    hora_entrada = fields.Float(
        string='Hora de Entrada',
        required=True,
        tracking=True
    )
    hora_salida = fields.Float(
        string='Hora de Salida',
        tracking=True
    )

    # Campos de contacto
    telefono_contacto = fields.Char(
        string='Teléfono de Contacto',
        required=True,
        tracking=True
    )
    contacto_emergencia = fields.Char(
        string='Contacto de Emergencia',
        tracking=True
    )

    # Estado del servicio
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado')
    ], string='Estado', default='borrador', tracking=True)

    # Campos específicos de guardería
    comportamiento = fields.Text(
        string='Cambios de Comportamiento',
        tracking=True
    )
    incidentes = fields.Text(
        string='Incidentes',
        tracking=True
    )
    alimentacion = fields.Selection([
        ('completa', 'Comió Todo'),
        ('parcial', 'Comió Parcialmente'),
        ('no_comio', 'No Comió')
    ], string='Alimentación', tracking=True)
    siesta = fields.Selection([
        ('si', 'Sí durmió'),
        ('no', 'No durmió'),
        ('parcial', 'Durmió poco')
    ], string='Siesta', tracking=True)

    # Campos específicos de lectura
    nivel_participacion = fields.Selection([
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta')
    ], string='Nivel de Participación', tracking=True)
    tema_lectura = fields.Char(
        string='Tema de Lectura',
        tracking=True
    )
    comprension = fields.Selection([
        ('excelente', 'Excelente'),
        ('buena', 'Buena'),
        ('regular', 'Regular'),
        ('necesita_apoyo', 'Necesita Apoyo')
    ], string='Nivel de Comprensión', tracking=True)

    # Campos comunes
    observaciones = fields.Text(
        string='Observaciones',
        tracking=True
    )
    requiere_seguimiento = fields.Boolean(
        string='Requiere Seguimiento',
        tracking=True
    )
    motivo_seguimiento = fields.Text(
        string='Motivo del Seguimiento',
        tracking=True
    )

    @api.constrains('hora_entrada', 'hora_salida')
    def _check_hora_entrada(self):
        for record in self:
            if (record.hora_entrada < 0 or record.hora_entrada >= 24) or (record.hora_salida and (record.hora_salida < 0 or record.hora_salida >= 24)):
                raise UserError("La hora de entrada y la de salida debe estar entre 00:00 y 23:59.")

    def action_iniciar(self):
        for record in self:
            if record.hora_entrada == 0:
                raise UserError('Debe registrar la hora de entrada antes de iniciar.')
            record.write({'state': 'en_curso'})

    def action_finalizar(self):
        if not self.hora_salida:
            raise UserError('Debe registrar la hora de salida antes de finalizar.')
        self.write({'state': 'finalizado'})


    def action_borrador(self):
        self.write({'state': 'borrador'})

    @api.constrains('codigo')
    def _check_codigo(self):
        for record in self:
            if record.codigo:
                codigo_existente = self.search([('codigo', '=', record.codigo), ('id', '!=', record.id)], limit=1)
                if codigo_existente:
                    raise UserError('Este servicio ya genero una consulta con el mismo código.')

    @api.onchange('tipo_servicio')
    def _onchange_tipo_servicio(self):
        # Limpiar campos específicos cuando cambia el tipo de servicio
        if self.tipo_servicio == 'guarderia':
            self.nivel_participacion = False
            self.tema_lectura = False
            self.comprension = False
        elif self.tipo_servicio == 'lectura':
            self.alimentacion = False
            self.siesta = False

    @api.constrains('hora_entrada', 'hora_salida')
    def _check_horas(self):
        for record in self:
            if record.hora_salida and record.hora_entrada > record.hora_salida:
                raise UserError('La hora de salida debe ser posterior a la hora de entrada.')
            
    
            
    def create(self, vals):
        cuidado_child = super(MzCuidadoChild, self).create(vals)
        if 'codigo' in vals:
            self.env['mz.asistencia_servicio'].search([('codigo', '=', vals['codigo'])]).write({'atendido': True, 'cuidado_child_id': cuidado_child.id})
        else:
            raise UserError('No se ha generado el código de asistencia.')
        return cuidado_child
    
    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user
        if user.has_group('manzana_de_cuidados.group_mz_prestador_servicio') or \
            user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_cuidado_child_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_cuidado_child_form').id
        else:
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_cuidado_child_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_cuidado_child_form_limit').id


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
            if self._context.get('filtrar_cuidado'):                 
                # Verificar grupos
                employee_id = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
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
                        ('state', '=', 'finalizado')
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                elif user.has_group('manzana_de_cuidados.group_mz_prestador_servicio'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    if_cuidado_child = False
                    for servicio in employee_id.servicios_ids:
                        if servicio.servicio_id.tipo_servicio == 'cuidado_infantil':
                            if_cuidado_child = True
                            break
                    if if_cuidado_child:
                        programa_ids = self.with_context(disable_custom_search=True).search([
                                    '|',
                                        '&',
                                            ('programa_id', '=', user.programa_id.id),
                                            ('state', '=', 'finalizado'),
                                        ('personal_id', '=', employee_id.id)
                                    ]).ids
                        base_args = [('id', 'in', programa_ids)]
                    else:
                        base_args = [('id', 'in', [])]
                else :
                    # Para usuarios sin rol especial: ver solo sus propios programas
                    base_args = [('id', 'in', [])]

                args = base_args + args

        return super(MzCuidadoChild, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
    



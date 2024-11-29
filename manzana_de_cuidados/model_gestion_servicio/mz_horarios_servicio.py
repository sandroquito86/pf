# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

from string import ascii_letters, digits
import string
import datetime


class AsignacionHorarios(models.Model):
    _name = 'mz.horarios.servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Asignación de Horarios' 

    
    name = fields.Char(string='Nombre',  compute='_compute_name', store=True)
    
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.asignacion.servicio', ondelete='restrict', domain="[('programa_id', '=?', programa_id)]", required=True, tracking=True)
    programa_id = fields.Many2one('pf.programas', string='Programa', required=True, tracking=True, default=lambda self: self.env.programa_id) 
    asi_servicio_id = fields.Many2one(string='Servicios', comodel_name='mz.servicio', ondelete='restrict')
    domain_programa_id = fields.Char(string='Domain Programa',compute='_compute_domain_programas')
    personal_id = fields.Many2one(string='Personal', comodel_name='hr.employee', ondelete='restrict',)   
    domain_personal_id = fields.Char(string='Domain Personal',compute='_compute_author_domain_field') 
    active = fields.Boolean(default=True, string='Activo', tracking=True)   
    detalle_horario_ids = fields.One2many(string='Detalle Horarios', comodel_name='mz.detalle.horarios', inverse_name='asignacion_horario_id',)
    if_admin = fields.Boolean(string='Es administrador', compute='_compute_if_administrador', default=False)

    @api.depends('servicio_id')
    def _compute_if_administrador(self):
        for record in self:
            # Captura los permisos del que esta logeado y valida si tiene el permiso de sistemas
            groups = self.env.user.groups_id
            if self.env.ref('manzana_de_cuidados.group_beneficiario_manager') in groups:
                record.if_admin = True
            else:
                record.if_admin = False

    @api.onchange('servicio_id')
    def _onchange_if_administrador(self):
        for record in self:
            groups = self.env.user.groups_id
            if self.env.ref('manzana_de_cuidados.group_beneficiario_manager') in groups:
                record.if_admin = True
            else:
                record.if_admin = False

    @api.onchange('programa_id')
    def _onchange_programa_id(self):
        for record in self:
            record.asi_servicio_id = False
            record.servicio_id = False
            record.personal_id = False
            record.detalle_horario_ids = False


    @api.onchange('servicio_id')
    def _onchange_servicio_id(self):
        for record in self:
            record.personal_id = False
            record.detalle_horario_ids = False

    @api.onchange('personal_id')
    def _onchange_personal_id(self):
        for record in self:
            record.detalle_horario_ids = False
   
    @api.depends('servicio_id')
    def _compute_domain_programas(self):
        for record in self:
            programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)])
            if programas:
                record.domain_programa_id = [('id', 'in', programas.ids)]
            else:
                record.domain_programa_id = [('id', 'in', [])]
    
    @api.depends('servicio_id')
    def _compute_name(self):
        for record in self:
            if record.servicio_id:
                record.name = f'Horario de {record.servicio_id.name}'
                record.asi_servicio_id = record.servicio_id.servicio_id.id
            else:
                record.name = 'Horario de Servicio'


    _sql_constraints = [('name_unique', 'UNIQUE(servicio_id,personal_id)', "Ya existe un horario para esta persona, en este servicio.")]    

    @api.depends('servicio_id')
    def _compute_author_domain_field(self):
        for record in self:
            if record.servicio_id:
                empleados = self.env['mz.asignacion.servicio'].search([('id', '=', record.servicio_id.id)]).mapped('personal_ids')
                if empleados:
                    record.domain_personal_id = [('id', 'in', empleados.ids)]
                else:
                    record.domain_personal_id = [('id', 'in', [])]
            else:
                record.domain_personal_id = [('id', 'in', [])]

    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user

        if user.has_group('manzana_de_cuidados.group_coordinador_manzana') or \
        user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_horarios_servicio_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_horarios_servicio_form').id
        else:
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_horarios_servicio_tree_limit').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_horarios_servicio_form_limit').id

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
        Método _search personalizado para filtrar programas cuando viene el contexto
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
                
                elif user.has_group('manzana_de_cuidados.group_coordinador_manzana') or \
                    user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia')  or \
                    user.has_group('manzana_de_cuidados.group_mz_registro_informacion'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id', '=', user.programa_id.id)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                else :
                    # Para usuarios sin rol especial: ver solo sus propios programas
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('personal_id', '=', user.employee_id.id)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]

                args = base_args + args

        return super(AsignacionHorarios, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)


class DetalleHorarios(models.Model):
    _name = 'mz.detalle.horarios'
    _description = 'Detalle de Horarios'
    _order = 'fecha, horainicio ASC'    
                

    asignacion_horario_id = fields.Many2one(string='Cabecera', comodel_name='mz.horarios.servicio', ondelete='restrict', required=True)
    fecha = fields.Date(string='Fecha', required=True, default=fields.Datetime.now, )
    horainicio = fields.Float(string='Hora Inicio', required=True, )
    horafin = fields.Float(string='Hora Fin', required=True, )       
    hora = fields.Char(string='Hora')
    estado = fields.Boolean(default='True')    
    observacion = fields.Char(string='Observación')
    fecha_actualizacion = fields.Date(string='Fecha Actualiza', readonly=True, default=fields.Datetime.now, )
    dias = fields.Selection([('0', 'LUNES'), ('1', 'MARTES'), ('2', 'MIERCOLES'), ('3', 'JUEVES'), ('4', 'VIERNES'), 
                                                            ('5', 'SABADO'), ('6', 'DOMINGO')],string='Dia', 
                                                            required=True, )
    property_valuation = fields.Selection([
        ('manual_periodic', 'Manual'),
        ('real_time', 'Automated')], string='Inventory Valuation',
        company_dependent=True, copy=True, required=True,
        help="""Manual: The accounting entries to value the inventory are not posted automatically.
        Automated: An accounting entry is automatically created to value the inventory when a product enters or leaves the company.
        """)
    duracionconsulta = fields.Float(string='Duración del Servicio', required=True, )

    _sql_constraints = [('name_unique', 'UNIQUE(asignacion_horario_id,dias)', "No se permiten días repetidos.")]  

    @api.constrains('horainicio', 'horafin')
    def _check_hora_entrada(self):
        for record in self:
            if (record.horainicio < 0 or record.horainicio >= 24) or (record.horafin < 0 or record.horafin >= 24):
                raise UserError("La hora de inicio y fin debe estar entre 00:00 y 23:59.")

    @api.onchange('dias')
    def _onchange_dias(self):
        if self.dias:
            registros = self.env['mz.detalle.horarios'].search([('asignacion_horario_id', '=', self.asignacion_horario_id._origin.id)]).mapped('dias')
            if self.dias in registros:
                raise ValidationError('No se permiten días repetidos.')
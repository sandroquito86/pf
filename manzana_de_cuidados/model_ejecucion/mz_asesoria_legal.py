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

class MzAsesoriaLegal(models.Model):
    _name = 'mz.asesoria.legal'
    _description = 'Gestión de Asesorías Legales'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, hora_inicio desc'
    _rec_name = 'codigo'

    # Campos de identificación y control
    codigo = fields.Char(string='Código', required=True, store=True)

    @api.model
    def _get_tipo_asesoria_domain(self):
        catalogo_id = self.env.ref('prefectura_base.catalogo_tipo_asesoria').id
        return [('catalogo_id', '=', catalogo_id)]
    
    @api.model
    def _get_causa_legal_domain(self):
        catalogo_id = self.env.ref('prefectura_base.catalogo_causa_legal').id
        return [('catalogo_id', '=', catalogo_id)]

    tipo_asesoria_id = fields.Many2one('pf.items', string='Tipo de Asesoría',domain=_get_tipo_asesoria_domain,  tracking=True )
    causa_legal_id = fields.Many2one('pf.items', string='Causa Legal',domain=_get_causa_legal_domain,  tracking=True )

    # Campos relacionales
    beneficiario_id = fields.Many2one(
        'mz.beneficiario',
        string='Beneficiario',
        required=True,
        tracking=True
    )
    servicio_id = fields.Many2one(
        string='Servicio',
        comodel_name='mz.asignacion.servicio',
        ondelete='restrict'
    )
    asesor_id = fields.Many2one(
        'hr.employee',
        string='Asesor Jurídico',
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
    hora_inicio = fields.Float(
        string='Hora de Inicio',
        required=True,
        tracking=True
    )
    hora_fin = fields.Float(
        string='Hora de Fin',
        tracking=True
    )
    duracion = fields.Float(
        string='Duración (horas)',
        compute='_compute_duracion',
        store=True
    )

    # Campos de contacto
    telefono_contacto = fields.Char(
        string='Teléfono de Contacto',
        required=True,
        tracking=True
    )

    # Estado de la asesoría
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado'),
    ], string='Estado', default='borrador', tracking=True)

    # Campos específicos de la asesoría
    descripcion_caso = fields.Text(
        string='Descripción del Caso',
        required=True,
        tracking=True
    )
    documentos_presentados = fields.Text(
        string='Documentos Presentados',
        tracking=True
    )
    recomendaciones = fields.Text(
        string='Recomendaciones',
        tracking=True
    )
    pasos_seguir = fields.Text(
        string='Pasos a Seguir',
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
    prioridad = fields.Selection([
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente')
    ], string='Prioridad del Caso', default='media', tracking=True)

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_duracion(self):
        for record in self:
            if record.hora_inicio and record.hora_fin:
                record.duracion = record.hora_fin - record.hora_inicio
            else:
                record.duracion = 0.0

    @api.constrains('hora_inicio', 'hora_fin')
    def _check_horas(self):
        for record in self:
            if record.hora_fin and record.hora_inicio > record.hora_fin:
                raise UserError('La hora de fin debe ser posterior a la hora de inicio.')
            if (record.hora_inicio < 0 or record.hora_inicio >= 24) or \
               (record.hora_fin and (record.hora_fin < 0 or record.hora_fin >= 24)):
                raise UserError('Las horas deben estar entre 00:00 y 23:59.')
            
    @api.depends('fecha')
    def _compute_hora_inicio(self):
        for record in self:
            user_tz = self.env.user.tz or 'UTC'  # Obtiene la zona horaria del usuario o usa 'UTC' por defecto
            local_tz = pytz.timezone(user_tz)
            ahora = datetime.now(pytz.utc).astimezone(local_tz)  # Convierte la hora actual a la zona horaria del usuario
            record.hora_inicio = ahora.hour + ahora.minute / 60.0

    def action_iniciar(self):
        for record in self:
            if record.hora_inicio == 0:
                raise UserError('Debe registrar la hora de inicio antes de comenzar.')
            record.write({'state': 'en_curso'})

    def action_finalizar(self):
        if not self.hora_fin:
            raise UserError('Debe registrar la hora de fin antes de finalizar.')
        self.write({'state': 'finalizado'})

    def action_borrador(self):
        self.write({'state': 'borrador'})

    @api.constrains('codigo')
    def _check_codigo(self):
        for record in self:
            if record.codigo:
                codigo_existente = self.search([
                    ('codigo', '=', record.codigo),
                    ('id', '!=', record.id)
                ], limit=1)
                if codigo_existente:
                    raise UserError('Ya existe una asesoría con el mismo código.')

    def create(self, vals):
        asesoria = super(MzAsesoriaLegal, self).create(vals)
        if 'codigo' in vals:
            self.env['mz.asistencia_servicio'].search([
                ('codigo', '=', vals['codigo'])
            ]).write({
                'atendido': True,
                'asesoria_legal_id': asesoria.id
            })
        else:
            raise UserError('No se ha generado el código de asistencia.')
        return asesoria
    

    

    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user
        if user.has_group('manzana_de_cuidados.group_mz_prestador_servicio') or \
            user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_asesoria_legal_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_asesoria_legal_form').id
        else:
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_asesoria_legal_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_asesoria_legal_form_limit').id


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
        base_args = [('id', 'in', [])]
        
        # Evitar recursión usando un contexto especial
        if not self._context.get('disable_custom_search'):
            if self._context.get('filtrar_asesoria'):                   
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
                        ('state', '=', 'finalizado')
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                elif user.has_group('manzana_de_cuidados.group_mz_prestador_servicio'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    if_asesoria = False
                    for servicio in user.employee_id.servicios_ids:
                        if servicio.servicio_id.tipo_servicio == 'asesoria_legal':
                            if_asesoria = True
                            break
                    if if_asesoria:
                        employee_id = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
                        programa_ids = self.with_context(disable_custom_search=True).search([
                                    '|',
                                        '&',
                                            ('programa_id', '=', user.programa_id.id),
                                            ('state', '=', 'finalizado'),
                                        ('asesor_id', '=', employee_id.id)
                                    ]).ids
                        base_args = [('id', 'in', programa_ids)]

                args = base_args + args

        return super(MzAsesoriaLegal, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class AsistenciaServicio(models.Model):
    _name = 'mz.asistencia_servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Asistencia a Servicios Planificados'
    _rec_name = 'beneficiario_id'

    planificacion_id = fields.Many2one('mz.planificacion.servicio', string='Planificación', required=True, ondelete='cascade')
    beneficiario_id = fields.Many2one('mz.beneficiario', string='Beneficiario', required=True)
    tipo_beneficiario = fields.Selection([('titular', 'Titular'),('dependiente', 'Dependiente') ], string='Tipo de Beneficiario', default='titular') 
    mascota_id = fields.Many2one('mz.mascota', string='Mascota')   
    dependiente_id = fields.Many2one('mz.dependiente', string='Dependiente')
    fecha = fields.Date('Fecha')
    asistio = fields.Selection([('si', 'Si'), ('no', 'No'), ('pendiente', 'Pendiente')], string='Asistió', default='pendiente')
    atendido = fields.Boolean(string='Atendido', default=False)
    observacion = fields.Text(string='Observación')
    programa_id = fields.Many2one('pf.programas', string='Programa', required=True)
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.asignacion.servicio', ondelete='restrict')
    servicio_base_id = fields.Many2one(string='Servicios', comodel_name='mz.servicio', ondelete='restrict', related='servicio_id.servicio_id', store=True)
    personal_id = fields.Many2one(string='Personal', comodel_name='hr.employee', ondelete='restrict') 
    codigo = fields.Char(string='Código', readonly=True, store=True)
    if_consulta_medica = fields.Boolean(string='Consulta Médica', compute='_compute_if_consulta_medica')
    if_consulta_psicologica = fields.Boolean(string='Consulta Psicológica', compute='_compute_if_consulta_psicologica')
    cuidado_child_id = fields.Many2one('mz.cuidado.child', string='Cuidado Infantil')
    tipo_servicio = fields.Selection([('normal', 'Bienestar Personal'), ('medico', 'Salud'), ('cuidado_infantil', 'Cuidado Infantil'), ('mascota', 'Mascota'), ('asesoria_legal', 'Asesoria Legal')], string='Clasificación de Servicio', compute='_compute_tipo_servicio')
    consulta_id = fields.Many2one('mz.consulta', string='Consulta Médica')
    consulta_psicologica_id = fields.Many2one('mz.consulta.psicologica', string='Consulta Psicológica')
    cuidado_child_id = fields.Many2one('mz.cuidado.child', string='Cuidado Infantil')
    asesoria_legal_id = fields.Many2one('mz.asesoria.legal', string='Asesoría Legal')
    servicio_veterinario_id = fields.Many2one('mz.servicio.veterinario', string='Servicio Veterinario')
    active = fields.Boolean(string='Activo', default=True)
    sub_servicio_id = fields.Many2one(comodel_name='mz.sub.servicio', string='Sub Servicio',domain="[('servicio_id', '=', servicio_id)]")


    # Signos vitales
    presion_arterial = fields.Char(
        string="Presión Arterial",
        compute="_compute_presion_arterial",
        store=True
    )
    presion_sistolica = fields.Integer(string="Presión Sistólica")
    presion_diastolica = fields.Integer(string="Presión Diastólica")
    frecuencia_cardiaca = fields.Integer(string='Frecuencia Cardíaca')
    frecuencia_respiratoria = fields.Integer(string='Frecuencia Respiratoria')
    temperatura = fields.Float(string='Temperatura (°C)')
    peso = fields.Float(string='Peso (kg)')
    altura = fields.Float(string='Altura (cm)')
    imc = fields.Float(string='IMC', compute='_compute_imc')

    _sql_constraints = [
        ('unique_planificacion_beneficiario', 'unique(planificacion_id, beneficiario_id)', 
         'Ya existe un registro de asistencia para este beneficiario en esta planificación.'),
         ('unique_codigo', 'unique(codigo)', 'El código de asistencia debe ser único.')]
    
    @api.depends('peso', 'altura')
    def _compute_imc(self):
        for record in self:
            if record.peso and record.altura:
                altura_m = record.altura / 100  # convertir cm a m
                record.imc = record.peso / (altura_m * altura_m)
            else:
                record.imc = 0

    @api.depends('servicio_id')
    def _compute_tipo_servicio(self):
        for record in self:
            record.tipo_servicio = record.servicio_id.servicio_id.tipo_servicio

    @api.depends('presion_sistolica', 'presion_diastolica')
    def _compute_presion_arterial(self):
        for record in self:
            if record.presion_sistolica and record.presion_diastolica:
                record.presion_arterial = f"{record.presion_sistolica}/{record.presion_diastolica}"
            else:
                record.presion_arterial = "N/A"
                
    @api.depends('servicio_id')
    def _compute_if_consulta_medica(self):
        for record in self:
            record.if_consulta_medica = record.servicio_id.servicio_id.if_consulta_medica

    @api.depends('servicio_id')
    def _compute_if_consulta_psicologica(self):
        for record in self:
            record.if_consulta_psicologica = record.servicio_id.servicio_id.if_consulta_psicologica

    def action_asistio(self):
        self.asistio = 'si'
        self.env['mz.agendar_servicio'].search([('codigo', '=', self.codigo)]).write({'state': 'atendido'})
        self.planificacion_id.write({'estado': 'concluido'})
        if not self.fecha == fields.Date.today():
            pass
            # raise UserError('No puede dar asistencia a un servicio que no es del día de hoy.')
        

    def action_no_asistio(self):
        self.asistio = 'no'

    def action_ver_consulta(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consulta Médica',
            'res_model': 'mz.consulta',
            'view_mode': 'form',
            'res_id': self.consulta_id.id,
            'target': 'new',
            'views': [(self.env.ref('manzana_de_cuidados.view_mz_consulta_form_custom').id, 'form')],
            'context': {'form_view_initial_mode': 'readonly'},
        }
    
    def action_ver_consulta_psicologica(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consulta Psicológica',
            'res_model': 'mz.consulta.psicologica',
            'view_mode': 'form',
            'res_id': self.consulta_psicologica_id.id,
            'target': 'new',
            'views': [(self.env.ref('manzana_de_cuidados.view_mz_consulta_psicologica_form_read').id, 'form')],
            'context': {'form_view_initial_mode': 'readonly'},
        }
    
    def action_ver_cuidado_child(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cuidado Infantil',
            'res_model': 'mz.cuidado.child',
            'view_mode': 'form',
            'res_id': self.cuidado_child_id.id,
            'target': 'new',
            'views': [(self.env.ref('manzana_de_cuidados.view_mz_cuidado_child_form').id, 'form')],
            'context': {'form_view_initial_mode': 'readonly'},
        }
    
    def action_ver_asesoria_legal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asesoría Legal',
            'res_model': 'mz.asesoria.legal',
            'view_mode': 'form',
            'res_id': self.asesoria_legal_id.id,
            'target': 'new',
            'views': [(self.env.ref('manzana_de_cuidados.view_mz_asesoria_legal_form').id, 'form')],
            'context': {'form_view_initial_mode': 'readonly'},
        }
    
    def action_ver_servicio_mascota(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Serrvicio Veterinario',
            'res_model': 'mz.servicio.veterinario',
            'view_mode': 'form',
            'res_id': self.servicio_veterinario_id.id,
            'target': 'new',
            'views': [(self.env.ref('manzana_de_cuidados.view_mz_servicio_veterinario_form').id, 'form')],
            'context': {'form_view_initial_mode': 'readonly'},
        }
    
    def ingresar_signos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ingreso de Signos Vitales',
            'res_model': 'mz.asistencia_servicio',
            'view_mode': 'form',
            'views': [(self.env.ref('manzana_de_cuidados.view_asistencia_servicio_signos_vitales_form').id, 'form')],
            'res_id': self.id,
            'target': 'new',
        }
    
    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user

        if user.has_group('manzana_de_cuidados.group_mz_prestador_servicio') or \
        user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_asistencia_servicio_tree').id
        elif user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia') or \
             user.has_group('manzana_de_cuidados.group_mz_registro_informacion') or \
             user.has_group('manzana_de_cuidados.group_coordinador_manzana'):
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_asistencia_servicio_tree_limit').id

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
            if self._context.get('filtrar_asistencia'):                   
                # Verificar grupos
                if user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
                    # Para coordinador: ver solo programas de módulo 2
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id.modulo_id', '=', 2)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                elif user.has_group('manzana_de_cuidados.group_mz_registro_informacion') or \
                    user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia') or \
                    user.has_group('manzana_de_cuidados.group_coordinador_manzana'):
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

        return super(AsistenciaServicio, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

class PlanificacionServicio(models.Model):
    _inherit = 'mz.planificacion.servicio'

    generar_horario_id = fields.Many2one(string='detalle', comodel_name='mz.genera.planificacion.servicio', ondelete='restrict')  
    beneficiarios_count = fields.Integer(string='Número de Beneficiarios', compute='_compute_beneficiarios_count',store=True)
    asistencia_ids = fields.One2many('mz.asistencia_servicio', 'planificacion_id', string='Asistencias')

    @api.constrains('asistencia_ids', 'maximo_beneficiarios')
    def _check_maximo_beneficiarios(self):
        for record in self:
            if record.beneficiarios_count > record.maximo_beneficiarios:
                raise UserError(f"No se puede exceder el número máximo de beneficiarios ({record.maximo_beneficiarios}) para este horario.")

    @api.depends('asistencia_ids')
    def _compute_beneficiarios_count(self):
        for record in self:
            record.beneficiarios_count = len(record.asistencia_ids)


    

    # @api.depends('fecha', 'horainicio')
    # def _compute_horario(self):
    #     for record in self:
    #         if record.fecha and record.horainicio:
    #             hora = timedelta(hours=record.horainicio)
    #             record.horario = f"{record.fecha} (hora inicio {hora.seconds // 3600:02d}:{(hora.seconds // 60) % 60:02d})"
    #         else:
    #             record.horario = False

 
   
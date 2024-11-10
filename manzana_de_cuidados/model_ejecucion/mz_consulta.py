# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta
from random import randint
from datetime import datetime
from odoo.exceptions import UserError
import pytz

class Consulta(models.Model):
    _name = 'mz.consulta'
    _description = 'Consulta Médica'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'codigo'
    _order = 'fecha desc, hora desc'

    codigo = fields.Char(string='Código', readonly=True, store=True)
    fecha = fields.Date(string='Fecha', required=True, tracking=True)
    hora = fields.Float(string='Hora', required=True, tracking=True, compute='_compute_hora', store=True)
    beneficiario_id = fields.Many2one(string='Beneficiario', comodel_name='mz.beneficiario', ondelete='restrict', tracking=True, required=True)
    programa_id = fields.Many2one('pf.programas', string='Programa', required=True, default=lambda self: self.env.programa_id)
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.asignacion.servicio', ondelete='restrict', domain="[('programa_id', '=?', programa_id)]")
    personal_id = fields.Many2one(string='Personal Médico', comodel_name='hr.employee', ondelete='restrict', tracking=True)
    asistencia_servicio_id = fields.Many2one('mz.asistencia.servicio', string='Asistencia Servicio')
    # Información del paciente
    genero = fields.Selection([
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('otro', 'Otro')
    ], string='Género')
    fecha_nacimiento = fields.Date(string='Fecha de Nacimiento', tracking=True)
    edad = fields.Char(string="Edad", compute="_compute_edad")
    
    # Motivo de consulta y síntomas
    motivo_consulta = fields.Text(string='Motivo de Consulta', required=True, tracking=True)
    sintomas = fields.Text(string='Síntomas', tracking=True)
    
    # Signos vitales
    presion_arterial = fields.Char(
        string="Presión Arterial",
        compute="_compute_presion_arterial",
        store=True
    )
    presion_sistolica = fields.Integer(string="Presión Sistólica", tracking=True)
    presion_diastolica = fields.Integer(string="Presión Diastólica", tracking=True)
    frecuencia_cardiaca = fields.Integer(string='Frecuencia Cardíaca', tracking=True)
    frecuencia_respiratoria = fields.Integer(string='Frecuencia Respiratoria', tracking=True)
    temperatura = fields.Float(string='Temperatura (°C)', tracking=True)
    peso = fields.Float(string='Peso (kg)', tracking=True)
    altura = fields.Float(string='Altura (cm)', tracking=True)
    imc = fields.Float(string='IMC', compute='_compute_imc', store=True)
    
    # Examen físico
    examen_fisico = fields.Text(string='Examen Físico', tracking=True)
    
    # Diagnóstico y tratamiento
    # Reemplazar los campos anteriores con la nueva relación
    diagnostico_ids = fields.One2many(
        'mz.diagnostico.linea',
        'consulta_id',
        string='Diagnósticos'
    )
    tratamiento = fields.Text(string='Tratamiento', tracking=True)
    
    # Historial médico
    antecedentes_personales = fields.Text(string='Antecedentes Personales', tracking=True)
    antecedentes_familiares = fields.Text(string='Antecedentes Familiares', tracking=True)
    alergias = fields.Text(string='Alergias', tracking=True)
    medicamentos_actuales = fields.Text(string='Medicamentos Actuales', tracking=True)
    
    # Seguimiento
    observaciones = fields.Text(string='Observaciones', tracking=True)
    proxima_cita = fields.Date(string='Próxima Cita', tracking=True)

    historia_clinica_id = fields.Many2one('mz.historia.clinica', string='Historia Clínica', readonly=True)


    receta_ids = fields.One2many('mz.receta.linea', 'consulta_id', string='Receta Médica')
    picking_id = fields.Many2one('stock.picking', string='Orden de Entrega', readonly=True)

    # Añadimos campo computado para contar historias clínicas
    historial_count = fields.Integer(
        string='Cantidad de Historias',
        compute='_compute_historial_count'
    )
    
    # Campo relacionado para acceder a las historias clínicas del beneficiario
    historial_ids = fields.One2many(
        related='beneficiario_id.historia_clinica_ids',
        string='Historias Clínicas'
    )
    
    
    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'El código de la consulta debe ser único.')
    ]

    @api.constrains('diagnostico_ids')
    def _check_diagnosticos(self):
        for record in self:
            if not record.diagnostico_ids:
                raise UserError('Debe ingresar al menos un diagnóstico.')
            
            # Verificar que haya exactamente un diagnóstico principal
            principales = record.diagnostico_ids.filtered(lambda d: d.es_principal)
            if len(principales) != 1:
                raise UserError('Debe haber exactamente un diagnóstico principal.')
            
    @api.depends('presion_sistolica', 'presion_diastolica')
    def _compute_presion_arterial(self):
        for record in self:
            if record.presion_sistolica and record.presion_diastolica:
                record.presion_arterial = f"{record.presion_sistolica}/{record.presion_diastolica}"
            else:
                record.presion_arterial = "N/A"
   

    @api.constrains('codigo')
    def _check_codigo(self):
        for record in self:
            if record.codigo:
                codigo_existente = self.search([('codigo', '=', record.codigo), ('id', '!=', record.id)], limit=1)
                if codigo_existente:
                    raise UserError('Este servicio ya genero una consulta con el mismo código.')
                
    @api.depends('beneficiario_id')
    def _compute_historial_count(self):
        for record in self:
            record.historial_count = len(record.beneficiario_id.historia_clinica_ids)
    
    def action_view_historial(self):
        self.ensure_one()
        return {
            'name': f'Historial Clínico - {self.beneficiario_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'mz.historia.clinica',
            'view_mode': 'tree,form',
            'domain': [('beneficiario_id', '=', self.beneficiario_id.id)],
            'context': {
                'default_beneficiario_id': self.beneficiario_id.id,
                'search_default_beneficiario_id': self.beneficiario_id.id,
            },
            'target': 'current',
        }


    @api.model
    def default_get(self, fields_list):
        defaults = super(Consulta, self).default_get(fields_list)
        
        context = self.env.context
        defaults['personal_id'] = context.get('default_personal_id')
        defaults['beneficiario_id'] = context.get('default_beneficiario_id')
        defaults['servicio_id'] = context.get('default_servicio_id')
        defaults['programa_id'] = context.get('default_programa_id')
        defaults['fecha'] = context.get('default_fecha')
        
        if defaults.get('beneficiario_id'):
            beneficiario = self.env['mz.beneficiario'].browse(defaults['beneficiario_id'])
            defaults['genero'] = beneficiario.genero
            defaults['fecha_nacimiento'] = beneficiario.fecha_nacimiento
        
             # Obtener el registro más reciente de mz.consulta para el beneficiario
            consulta_reciente = self.search([('beneficiario_id', '=', beneficiario.id)], order='fecha desc, hora desc', limit=1)
            if consulta_reciente:
                defaults['antecedentes_personales'] = consulta_reciente.antecedentes_personales
                defaults['antecedentes_familiares'] = consulta_reciente.antecedentes_familiares
                defaults['alergias'] = consulta_reciente.alergias
                defaults['medicamentos_actuales'] = consulta_reciente.medicamentos_actuales
        return defaults

    @api.depends('fecha_nacimiento')
    def _compute_edad(self):
        for record in self:
            if record.fecha_nacimiento:
                hoy = date.today()
                diferencia = relativedelta(hoy, record.fecha_nacimiento)
                record.edad = f"{diferencia.years} años, {diferencia.months} meses, {diferencia.days} días"
            else:
                record.edad = "Sin fecha de nacimiento"

    @api.depends('fecha')
    def _compute_hora(self):
        for record in self:
            user_tz = self.env.user.tz or 'UTC'  # Obtiene la zona horaria del usuario o usa 'UTC' por defecto
            local_tz = pytz.timezone(user_tz)
            ahora = datetime.now(pytz.utc).astimezone(local_tz)  # Convierte la hora actual a la zona horaria del usuario
            record.hora = ahora.hour + ahora.minute / 60.0

    @api.depends('peso', 'altura')
    def _compute_imc(self):
        for record in self:
            if record.peso and record.altura:
                altura_m = record.altura / 100  # convertir cm a m
                record.imc = record.peso / (altura_m * altura_m)
            else:
                record.imc = 0

    
    

    def create(self, vals):
        consulta = super(Consulta, self).create(vals)
        consulta.crear_historia_clinica()
        self.env['mz.asistencia_servicio'].search([('codigo', '=', vals['codigo'])]).write({'atendido': True, 'consulta_id': consulta.id})
        return consulta

    def write(self, vals):
        res = super(Consulta, self).write(vals)
        self.actualizar_historia_clinica()
        return res

    def crear_historia_clinica(self):
        for consulta in self:
            historia_clinica = self.env['mz.historia.clinica'].create({
                'beneficiario_id': consulta.beneficiario_id.id,
                'consulta_id': consulta.id,
                'personal_id': consulta.personal_id.id,
                'sintomas': consulta.sintomas,
                'fecha': consulta.fecha,
                'motivo_consulta': consulta.motivo_consulta,
                'tratamiento': consulta.tratamiento,
                'observaciones': consulta.observaciones,
                'antecedentes_personales': consulta.antecedentes_personales,
                'antecedentes_familiares': consulta.antecedentes_familiares,
                'alergias': consulta.alergias,
                'medicamentos_actuales': consulta.medicamentos_actuales,
                'signos_vitales': f"PA: {consulta.presion_arterial}, FC: {consulta.frecuencia_cardiaca}, FR: {consulta.frecuencia_respiratoria}, Temp: {consulta.temperatura}"
            })
            consulta.historia_clinica_id = historia_clinica.id
            for diagnostico in consulta.diagnostico_ids:
                diagnostico.write({'historia_clinica_id': historia_clinica.id})

    def actualizar_historia_clinica(self):
        for consulta in self:
            if consulta.historia_clinica_id:
                consulta.historia_clinica_id.write({
                    'motivo_consulta': consulta.motivo_consulta,
                    'personal_id': consulta.personal_id.id,
                    'sintomas': consulta.sintomas,
                    'tratamiento': consulta.tratamiento,
                    'observaciones': consulta.observaciones,
                    'antecedentes_personales': consulta.antecedentes_personales,
                    'antecedentes_familiares': consulta.antecedentes_familiares,
                    'alergias': consulta.alergias,
                    'medicamentos_actuales': consulta.medicamentos_actuales,
                    'signos_vitales': f"PA: {consulta.presion_arterial}, FC: {consulta.frecuencia_cardiaca}, FR: {consulta.frecuencia_respiratoria}, Temp: {consulta.temperatura}"
                    
                })

    def generar_orden_entrega(self):
        self.ensure_one()
        
        if self.picking_id:
            raise UserError('Ya existe una orden de entrega para esta consulta.')
        
        productos_en_stock = self.receta_ids.filtered(lambda r: r.en_inventario)
        
        if productos_en_stock:
            # Buscar el tipo de operación para salidas
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'outgoing'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            
            if not picking_type:
                raise UserError('No se encontró un tipo de operación para salida de inventario.')
            
            # Verificar que las ubicaciones existan
            if not picking_type.default_location_src_id or not picking_type.default_location_dest_id:
                raise UserError('Las ubicaciones origen y destino no están configuradas en el tipo de operación.')
            
            # Asegurarse que el partner_id sea válido
            if not self.beneficiario_id.user_id.partner_id:
                raise UserError('El beneficiario no tiene un contacto asociado.')
            
            valores_picking = {
                'partner_id': self.beneficiario_id.user_id.partner_id.id,
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'origin': f'Consulta {self.codigo}',
                'company_id': self.env.company.id,
                'scheduled_date': fields.Datetime.now(),
                'move_type': 'direct',  # Entrega directa
                'state': 'draft',
            }
            
            # Crear el picking
            picking = self.env['stock.picking'].create(valores_picking)
            
            # Crear los movimientos de stock
            for linea in productos_en_stock:
                move_vals = {
                    'name': linea.producto_id.name,
                    'product_id': linea.producto_id.id,
                    'product_uom_qty': linea.cantidad,
                    'product_uom': linea.producto_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'company_id': self.env.company.id,
                    'state': 'draft',
                    'picking_type_id': picking_type.id,
                }
                self.env['stock.move'].create(move_vals)
            
            self.picking_id = picking.id
            return True
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Información',
                    'message': 'No se generó orden de entrega ya que no hay productos en stock.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
    
class MzDiagnosticoLinea(models.Model):
    _name = 'mz.diagnostico.linea'
    _description = 'Línea de Diagnóstico'

    consulta_id = fields.Many2one('mz.consulta', string='Consulta', required=True, ondelete='cascade')
    cie10_id = fields.Many2one('pf.cie10', string='Diagnóstico CIE-10', tracking=True)
    detalle = fields.Text(string='Detalle del diagnóstico')
    es_principal = fields.Boolean(string='Diagnóstico Principal', default=False)
    historia_clinica_id = fields.Many2one('mz.historia.clinica', string='Historia Clinica', ondelete='cascade')
    
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
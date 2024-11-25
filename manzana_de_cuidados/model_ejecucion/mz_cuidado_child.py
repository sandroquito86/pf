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
    




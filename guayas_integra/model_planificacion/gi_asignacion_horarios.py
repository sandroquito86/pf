# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from string import ascii_letters, digits
import string
import datetime


class AsignacionHorarios(models.Model):
    _name = 'gi.asignacion_horario'
    _description = 'Asignación de Horarios' 
    _rec_name = 'servicio_id'

    
    servicio_id = fields.Many2one(string='Servicio', comodel_name='gi.servicio', ondelete='restrict',)   
    personal_id = fields.Many2one(string='Personal', comodel_name='gi.personal', ondelete='restrict',)       
    detalle_horario_ids = fields.One2many(string='Detalle Horarios', comodel_name='gi.detalle_horarios', inverse_name='asignacion_horario_id',)
    
    
    

    _sql_constraints = [('name_unique', 'UNIQUE(servicio_id,personal_id)', "Ya existe una persona con este servicio.")]    




class DetalleGeneraHorarios(models.Model):
    _name = 'gi.detalle_horarios'
    _description = 'Detalle de Horarios'
    _order = 'fecha, horainicio ASC'    
                

    asignacion_horario_id = fields.Many2one(string='detalle', comodel_name='gi.asignacion_horario', ondelete='restrict',)
    fecha = fields.Date()
    horainicio = fields.Float(string='Hora Inicio')
    horafin = fields.Float(string='Hora Fin',)       
    hora = fields.Char(string='Hora')
    estado = fields.Boolean(default='True')    
    observacion = fields.Char(string='Observación')
    fecha_actualizacion = fields.Date(string='Fecha Actualiza', readonly=True, default=fields.Datetime.now, )
    dias = fields.Selection([('0', 'LUNES'), ('1', 'MARTES'), ('2', 'MIERCOLES'), ('3', 'JUEVES'), ('4', 'VIERNES'), 
                                                            ('5', 'SABADO'), ('6', 'DOMINGO')],string='Dia')
    property_valuation = fields.Selection([
        ('manual_periodic', 'Manual'),
        ('real_time', 'Automated')], string='Inventory Valuation',
        company_dependent=True, copy=True, required=True,
        help="""Manual: The accounting entries to value the inventory are not posted automatically.
        Automated: An accounting entry is automatically created to value the inventory when a product enters or leaves the company.
        """)
    duracionconsulta = fields.Float(string='Duración Consulta')

    _sql_constraints = [('name_unique', 'UNIQUE(asignacion_horario_id,diacons_ids)', "No se permiten días repetidos.")]    
    
   
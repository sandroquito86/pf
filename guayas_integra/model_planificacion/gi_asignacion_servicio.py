# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from string import ascii_letters, digits
import string


class AsignacionServicio(models.Model):
    _name = 'gi.asignacion_servicio'
    _description = 'Asignación de Servicios' 
    _rec_name = 'servicio_id'

    
    servicio_id = fields.Many2one(string='Servicio', comodel_name='gi.servicio', ondelete='restrict',)     
    personal_ids = fields.Many2many(string='Personal', comodel_name='gi.personal', relation='gi_asignacion_servicio_personal_rel', 
                                      column1='asignacion_servicio_id', column2='personal_id')
    

    _sql_constraints = [('name_unique', 'UNIQUE(servicio_id)', "El servicio no puede estar duplicado.")]    

   
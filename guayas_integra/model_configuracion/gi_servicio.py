# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from string import ascii_letters, digits
import string


class Servicios(models.Model):
    _name = 'gi.servicio'
    _description = 'Servicios'
    _order = 'name ASC'
    
    name = fields.Char(string='Servicio', required=True)    
    tipo_discapacidad_id = fields.Many2one(string='Tipo de Discapacidad', comodel_name='pf.tipo_discapacidad', ondelete='restrict')
    area_id = fields.Many2one(string='Área', comodel_name='gi.area', ondelete='restrict')
    
    @api.constrains('name')
    def _check_name(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe el servicio: %s , no se permiten valores duplicados" % (record.name.upper()))    
 

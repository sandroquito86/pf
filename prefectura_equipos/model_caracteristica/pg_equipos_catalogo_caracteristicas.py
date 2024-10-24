# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import models, fields, api
from string import ascii_letters, digits, whitespace


class CatalogoCaracteristica(models.Model):
    _name = 'pg_equipos.catalogo_caracteristica'
    _description = 'Catálogo Caractéristicas'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    
    name = fields.Char('Característica', required=True, tracking=True)  
    descripcion = fields.Text(string='Descripción', tracking=True )  
    caracteristica_valor_ids = fields.One2many(string='Valor Característica', comodel_name='pg_equipos.caracteristica_valor', inverse_name='caracteristica_id', )
    active = fields.Boolean(string='Activo/Inactivo', default='True' )
    
    _sql_constraints = [('name_unique', 'UNIQUE(name)', "Nombre de la característica debe ser único en cada categoría!!"),] 
    
    @api.constrains('name')
    def _check_name_categoria_activo(self):
        for record in self:            
            model_ids = record.search([('id', '!=',record.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe la caracteristica: %s , no se permiten valores duplicados" % (record.name.upper()))  
                
                  
class ValorCaracteristica(models.Model):
    _name = "pg_equipos.caracteristica_valor"   
    _order = 'caracteristica_id, sequence, id'
    _description = 'Valores de las Características'

    name = fields.Char(string='Valor', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', index=True)
    caracteristica_id = fields.Many2one('pg_equipos.catalogo_caracteristica', string="Valor", ondelete='restrict', index=True,)
    
    _sql_constraints = [('name_unique', 'UNIQUE(caracteristica_id,name)', "Valor debe ser único en cada característica!!!!"),] 
    
    @api.constrains('name')
    def _check_name_categoria_activo(self):
        for record in self:
            if(record.caracteristica_id):
                model_ids = record.search([('id', '!=',record.id),('caracteristica_id', '=',record.caracteristica_id.id)])        
                list_names = [x.name.upper() for x in model_ids if x.name]        
                if record.name.upper() in list_names:
                    raise ValidationError("Ya existe el valor: %s , no se permiten valores duplicados dentro de una misma característica" % (record.name.upper()))  

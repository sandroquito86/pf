# -*- coding: utf-8 -*-

##############################################################################
#

#
##############################################################################
from odoo.exceptions import ValidationError
from odoo import models, fields, api
from string import ascii_letters, digits, whitespace

class Catalogo(models.Model):
    _name = 'pf.catalogo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Catálogo'

    name = fields.Char(string="Nombre del Catalogo", required=True, tracking=True)
    items_ids = fields.One2many(string='Catalogo', comodel_name='pf.items', inverse_name='catalogo_id',)
    descripcion = fields.Char(string="descripcion", required=True)
    sequence = fields.Integer(
        'Secuencia', help="Usado para ordenar los catálogos.", default=1)
    active = fields.Boolean(
        string='Activo',
        default=True, tracking=True,
    )
    
    _sql_constraints = [('name_unique', 'UNIQUE(name)', "Catálogo debe ser único"),]    

  
class Items(models.Model):
    _name = 'pf.items'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Items'     

    name = fields.Char(string="Nombre del Item", help='Escriba el nombre del item asociado a su catálogo', required=True, tracking=True)   
    descripcion = fields.Char(string="Descripcion",  tracking=True )    
    catalogo_id = fields.Many2one(string='Catalogo', comodel_name='pf.catalogo', ondelete='restrict',required=True, tracking=True)   
       
    
    _sql_constraints = [('name_unique', 'UNIQUE(catalogo_id,name)', "Items debe ser único dentro de cada catálogo"),]    
    
    @api.constrains('name')
    def _check_name_marca_insensitive(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id),('catalogo_id', '=',record.catalogo_id.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe items: %s , no se permiten valores duplicados dentro del mismo catálogo" % (record.name.upper()))    
 
from odoo.exceptions import ValidationError
from odoo import models, fields, api
from string import ascii_letters, digits, whitespace
from lxml import etree

   
class Marca(models.Model): 
    _name = 'pg_equipos.marca'
    _description = 'Marca'
    _inherit = [ 'mail.thread' ,  'mail.activity.mixin' ]
    
    name = fields.Char(string='Marca',required=True, tracking=True)    
    modelo_ids = fields.One2many(string='Modelos', comodel_name='pg_equipos.modelo', inverse_name='marca_id',)    
    active = fields.Boolean(string='Activo/Inactivo', default='True' )
    
    _sql_constraints = [('name_unique', 'UNIQUE(name)', "Ya existe esta marca!!"),]

    @api.constrains('name')
    def _check_name_marca_insensitive(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe la marca: %s , no se permiten valores duplicados" % (record.name.upper())) 
    
              

class Modelo(models.Model): 
    _name = 'pg_equipos.modelo'
    _description = 'Modelo'
    _inherit = [ 'mail.thread' ,  'mail.activity.mixin' ]
    
    name = fields.Char('Modelo',required=True, tracking=True)
    marca_id = fields.Many2one(string='Marca', comodel_name='pg_equipos.marca', required=True, ondelete='restrict', tracking=True)  
    active = fields.Boolean(string='Activo/Inactivo', default='True' )
   
    _sql_constraints = [('name_unique', 'UNIQUE(marca_id,name)', "Ya existe este modelo dentro de la marca seleccionada!!"),]
    
    @api.constrains('name','marca_id')
    def _check_name_modelo_insensitive(self):       
        for record in self:
            model_ids = record.search([('id', '!=',record.id),('marca_id', '=',record.marca_id.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe el modelo: %s , no se permiten valores duplicados dentro de la misma marca!!" % (record.name.upper()))  
        
   
# -*- coding: utf-8 -*-

##############################################################################
#

#
##############################################################################
from odoo.exceptions import UserError
from odoo import models, fields, api
from string import ascii_letters, digits, whitespace

class Catalogo(models.Model):
    _name = 'mz.catalogo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Catálogo'

    name = fields.Char(string="Nombre del Catalogo", required=True, tracking=True)
    items_ids = fields.One2many(string='Catalogo', comodel_name='pf.items', inverse_name='catalogo_id',)
    descripcion = fields.Char(string="descripcion", required=True)
    sequence = fields.Integer(
        'Secuencia', help="Usado para ordenar los catálogos.", default=1)
    active = fields.Boolean(string='Activo', default=True, tracking=True,)
    
    _sql_constraints = [('name_unique', 'UNIQUE(name)', "Catálogo debe ser único"),]    

  
class Items(models.Model):
    _name = 'mz.items'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Items'     

    name = fields.Char(string="Nombre del Item", help='Escriba el nombre del item asociado a su catálogo', required=True, tracking=True)   
    descripcion = fields.Char(string="Descripcion", tracking=True )    
    catalogo_id = fields.Many2one(string='Catalogo', comodel_name='mz.catalogo', ondelete='restrict',required=True, tracking=True)   
    active = fields.Boolean(string='Activo', default=True, tracking=True,)   
    
    _sql_constraints = [('name_unique', 'UNIQUE(catalogo_id,name)', "Items debe ser único dentro de cada catálogo"),]    
    
    @api.constrains('name')
    def _check_name_marca_insensitive(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id),('catalogo_id', '=',record.catalogo_id.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise UserError("Ya existe items: %s , no se permiten valores duplicados dentro del mismo catálogo" % (record.name.upper()))    
 
    @api.constrains('catalogo_id')
    def _check_unique_item_per_catalogo_tipo(self):
        for record in self:
            # Solo aplica la restricción si el catálogo es de tipo "tipo_unico"
            tipo_unico_catalogo_id = self.env.ref('manzana_de_cuidados.codigo_prefectura').id
            if record.catalogo_id.id == tipo_unico_catalogo_id:
                # Contar cuántos items existen para este catálogo
                existing_items = self.search_count([
                    ('catalogo_id', '=', record.catalogo_id.id)
                ])
                # Si ya existe otro item en este tipo de catálogo, lanza un error
                if existing_items > 1:
                    raise UserError("Solo puede haber un único Item en este tipo de catálogo.")
from odoo.exceptions import ValidationError
from odoo import models, fields, api
from lxml import etree

class Catalogo(models.Model):
    _name = 'gi.catalogo'
    _description = 'Catálogo'

    name = fields.Char(string="Nombre del Catálogo", required=True)
    items_ids = fields.One2many(
        string='Items del Catálogo',
        comodel_name='gi.catalogo_items',
        inverse_name='catalogo_id'
    )
    
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', "El nombre del catálogo debe ser único.")
    ]    

    @api.constrains('name')
    def _check_name_marca_insensitive(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe el Catálogo: %s , no se permiten valores duplicados" % (record.name.upper())) 
    

class Items(models.Model):
    _name = 'gi.catalogo_items'
    #_inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Items'
    _order = "sequence"
    
    sequence = fields.Integer('Secuencia', help="Usado para ordenar los items.", default=1)
    name = fields.Char(string="Nombre del Item", required=True, tracking=True, help='Escriba el nombre del item asociado a su catálogo')
    descripcion = fields.Char(string="Descripción", tracking=True)
    catalogo_id = fields.Many2one(
        string='Catálogo',
        comodel_name='gi.catalogo',
        ondelete='restrict',
        required=True,
        tracking=True
    )
    active = fields.Boolean(string='Activo/Inactivo', default=True)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(catalogo_id,name)', "El nombre del ítem debe ser único dentro de cada catálogo.")
    ]

    @api.constrains('name')
    def _check_name_marca_insensitive(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id),('catalogo_id', '=',record.catalogo_id.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe el Catálogo: %s , no se permiten valores duplicados" % (record.name.upper())) 
    
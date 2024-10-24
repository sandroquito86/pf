from odoo.exceptions import ValidationError
from odoo import models, fields, api
from string import ascii_letters, digits, whitespace

class PermisoAcceso(models.Model):
    _name = 'asset.permiso_acceso'
    _description = 'Permisos de acceso'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']
    _rec_name = "programa_id"
    
    programa_id = fields.Many2one(string='Reparto', comodel_name='pf.programas', ondelete='restrict', required=True,) 

    grupo_id = fields.Many2one(string='Grupo', comodel_name='pg_equipos.grupo', required=True, ondelete='restrict', tracking=True)    
    categoria_ids = fields.Many2many(string='Categorías', comodel_name='pg_equipos.categoria', relation='asset_permiso_acceso_categoria_rel', column1='acceso_id', 
                                     column2='categoria_id',domain="[('grupo_id','=',grupo_id)]", required=True)    
    active = fields.Boolean(string='Activo/Inactivo', default='True' )
    
    _sql_constraints = [('reparto_unique', 'UNIQUE(programa_id,grupo_id)', "No se permite duplicidad de grupos en un mismo reparto!!")]    
    
    
        
        
        
        

    
  
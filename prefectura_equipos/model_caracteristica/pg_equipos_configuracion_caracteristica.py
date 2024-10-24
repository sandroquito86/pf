from odoo.exceptions import ValidationError
from odoo import models, fields, api
from string import ascii_letters, digits, whitespace

class ConfiguracionCaracteristica(models.Model):
    _name = 'pg_equipos.config_caracteristica'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']
    _description = 'Configuración Caracteristica Equipo'
    _rec_name = "grupo_id"     
   
    grupo_id = fields.Many2one(string='Grupo', comodel_name='pg_equipos.grupo', required=True, ondelete='restrict', tracking=True)  
    caracteristica_ids = fields.One2many(string='Caracteristicas', comodel_name='pg_equipos.caracteristica', inverse_name='config_caracteristica_activo_id',)
    active = fields.Boolean(string='Activo/Inactivo', default='True' )
    
    @api.onchange('grupo_id')
    def _onchange_grupo_id(self):
        self.caracteristica_ids = False 

    _sql_constraints = [('name_unique', 'UNIQUE(grupo_id)',"Ya existe un grupo creado, no puede ser duplicado"),] 
    

#Características obligatorias u opcionales
class Caracteristicas(models.Model):
    _name = "pg_equipos.caracteristica"    
    _description = 'Caracteristicas de Activo ' 
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'caracteristica_id'
   
    config_caracteristica_activo_id = fields.Many2one(string='Configuración caracteristicas activo', comodel_name='pg_equipos.config_caracteristica', required=True,
                                                      ondelete='restrict', tracking=True)  
    caracteristica_id_domain = fields.Char ( compute = "_compute_caracteristica_id_domain" , readonly = True, store = False, )
    caracteristica_id = fields.Many2one(string='Caracteristicas', comodel_name='pg_equipos.catalogo_caracteristica', 
                                  ondelete='restrict', required=True, tracking=True, )    
    es_obligatorio = fields.Boolean(string='Obligatorio', tracking=True)    
    
    @api.depends('caracteristica_id')
    def _compute_caracteristica_id_domain(self):
      for record in self:     
        record.caracteristica_id_domain = "[('id', '=', False)]"    
        if(record.config_caracteristica_activo_id):
            todas_caracteristicas = self.env['pg_equipos.catalogo_caracteristica'].search([])         
            caracteristicas_ingresadas = record.config_caracteristica_activo_id.caracteristica_ids.caracteristica_id 
            restantes = todas_caracteristicas - caracteristicas_ingresadas   
            record.caracteristica_id_domain = [('id', 'in', restantes.ids)]
            
            
      
  
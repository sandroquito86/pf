from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from dateutil.relativedelta import relativedelta

class Servicio(models.Model):
    _name = 'mz.servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Servicio'

    @api.model
    def _get_tipo_servicio_domain(self):
        catalogo_id = self.env.ref('manzana_de_cuidados.tipo_servicio').id
        return [('catalogo_id', '=', catalogo_id)]

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    active = fields.Boolean(default=True, string='Activo')
    if_derivacion = fields.Boolean(default=False, string='Derivación')
    image = fields.Binary(string='Imagen', attachment=True)
    tipo_servicio = fields.Selection([('normal', 'Normal'), ('medico', 'Medico')], string='Clasificación de Servicio', default='normal')
    catalogo_tipo_servicio_id = fields.Many2one('mz.items', string='Tipo de Servicio',  domain=_get_tipo_servicio_domain)
    sub_servicio_ids = fields.One2many('mz.sub.servicio', 'servicio_id', string='Sub Servicios')

    _sql_constraints = [('name_unique', 'UNIQUE(name)', "El servicio debe ser único"),]    
    
    @api.constrains('name')
    def _check_name_servicio(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise UserError("Ya existe el servicio: %s , no se permiten valores duplicados" % (record.name.upper()))    
 

        
class SubServicio(models.Model):
    _name = 'mz.sub.servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sub Servicio'

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    servicio_id = fields.Many2one('mz.servicio', string='Servicio', required=True, ondelete='cascade')
    active = fields.Boolean(default=True, string='Activo')  


    _sql_constraints = [('name_unique', 'UNIQUE(servicio_id,name)', "El subservicio debe ser único en cada servicio"),]    
    
    @api.constrains('name')
    def _check_name_sub_servicio(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id),('servicio_id', '=',record.servicio_id.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise UserError("Ya existe el subservicio: %s , no se permiten valores duplicados dentro del mismo servicio" % (record.name.upper()))    

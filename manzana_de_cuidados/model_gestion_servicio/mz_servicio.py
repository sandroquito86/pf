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

class SubServicio(models.Model):
    _name = 'mz.sub.servicio'
    _description = 'Sub Servicio'

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    servicio_id = fields.Many2one('mz.servicio', string='Servicio', required=True, ondelete='cascade')
    active = fields.Boolean(default=True, string='Activo')  

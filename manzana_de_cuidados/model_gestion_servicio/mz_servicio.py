from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from dateutil.relativedelta import relativedelta

class Servicio(models.Model):
    _name = 'mz.servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Servicio'

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    active = fields.Boolean(default=True, string='Activo')
    if_derivacion = fields.Boolean(default=False, string='Derivación')
    image = fields.Binary(string='Imagen', attachment=True)
    tipo_servicio = fields.Selection([('normal', 'Normal'), ('medico', 'Medico')], string='Tipo de Servicio', default='normal')
    

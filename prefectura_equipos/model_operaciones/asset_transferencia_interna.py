
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo import models, fields, api
import json
class TransferenciaInterna(models.Model): 
    _name = 'asset.transferencia_interna'
    _description = 'Transferencia Interna'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']
    # states={'borrador':[('readonly',False)]},
    fecha = fields.Datetime('Fecha ', required=False, readonly=True,  default=False, )
    personal_solicitante_id = fields.Many2one('hr.employee', string='Persona que solicita', default=lambda self: self.env.user.employee_id)
    personal_recibe_id = fields.Many2one('hr.employee', string='Persona que recibe', default=lambda self: self.env.user.employee_id)
                            
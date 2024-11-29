from odoo import models, fields, api
from odoo.exceptions import UserError

class PfProgramas(models.Model):
    _inherit = 'pf.programas'

    warehouse_ids = fields.One2many('stock.warehouse', 'programa_id', string='Almacenes')

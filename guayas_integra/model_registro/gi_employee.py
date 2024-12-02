from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

class GiEmployee(models.Model):
    _inherit = 'hr.employee'

    terapias_ids = fields.Many2many('gi.terapias', string="Terapias Asignadas")

    
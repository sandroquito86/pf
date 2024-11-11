from logging.config import valid_ident
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from babel.dates import format_date
# from datetime import datetime,time, datetime
from datetime import datetime
from datetime import date
import time
global NoTieneHorario

class PlanificacionServicio(models.Model):
    _inherit = 'mz.planificacion.servicio'

    asignacion_id = fields.Many2one('mz.asignacion.servicio', string='Asignación de Servicio', ondelete='restrict')
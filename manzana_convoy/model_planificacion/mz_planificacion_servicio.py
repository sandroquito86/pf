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


class GenerarHorarios(models.Model):
    _inherit = 'mz.genera.planificacion.servicio'

    @api.constrains('servicio_id', 'personal_id')
    def _check_detalle_generahorario(self):
        for record in self:           
            asignacion = self.env['mz.asignacion.servicio'].browse(record.servicio_id.id)                        
            if asignacion.convoy_id:
                continue                
            # Si no es de convoy, aplicamos la validación original
            if not (record.turno_disponibles_ids) and not record.es_replanificacion:
                raise UserError("No se puede guardar AGENDA sino genera detalle de Agenda!!")

# Tabla de horarios
class PlanificacionServicio(models.Model):
    _inherit = 'mz.planificacion.servicio'

    asignacion_id = fields.Many2one('mz.asignacion.servicio', string='Asignación de Servicio', ondelete='restrict')
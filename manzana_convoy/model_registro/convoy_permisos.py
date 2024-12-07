from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError

class MzConvoyOperadorPermisos(models.Model):
    _name = 'mz_convoy.permisos'
    _description = 'Permisos originales de operadores en convoy'
    _auto = True  # Crear tabla en la base de datos
    _log_access = False  # No necesitamos los campos de tracking estándar

    convoy_id = fields.Many2one('mz.convoy', 'Convoy', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Usuario', ondelete='cascade')     
    permisos_originales = fields.Many2many('res.groups', 'mz_convoy_operador_permisos_groups_rel','permiso_id', 'group_id', string='Permisos Originales' )
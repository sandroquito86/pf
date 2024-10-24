from odoo import models, fields, api

class PfModulo(models.Model):
    _name = 'pf.modulo'
    _description = 'Módulos disponibles en el sistema'

    name = fields.Char(string="Nombre del Módulo", required=True)
    color = fields.Integer(string="Color")
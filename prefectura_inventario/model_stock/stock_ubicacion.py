from odoo import models, fields, api

class StockLocation(models.Model):
    _inherit = 'stock.location'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', related='warehouse_id.programa_id', store=True)
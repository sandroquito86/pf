from odoo import models, fields, api

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    
    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', related='warehouse_id.programa_id', store=True)
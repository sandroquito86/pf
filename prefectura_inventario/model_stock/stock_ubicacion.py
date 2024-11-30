from odoo import models, fields, api

class StockLocation(models.Model):
    _inherit = 'stock.location'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', related='warehouse_id.programa_id', store=True)
    domain_location_general_id = fields.Char(string='Domain Location', compute='_compute_domain_location')

    @api.depends('warehouse_id')
    def _compute_domain_location(self):
        for record in self:
            # user = self.env.user
            # es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            # es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            # if es_coordinador:
            #     if user.programa_id:
            #         # Solo ve ubicaciones de su programa
            #         record.domain_location_general_id = [('programa_id', '=', user.programa_id.id)]
            #     else:
            #         record.domain_location_general_id = [('id', '=', False)]
            # elif es_sistema:
            #     # Si hay almacén seleccionado, filtra por ese almacén
            #     if record.warehouse_id:
            #         record.domain_location_general_id = [
            #             ('warehouse_id', '=', record.warehouse_id.id),
            #             ('programa_id', '!=', False)
            #         ]
            #     else:
            #         programas = self.env['pf.programas'].search([
            #             ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
            #         ])
            #         record.domain_location_general_id = [
            #             ('programa_id', 'in', programas.ids)
            #         ] if programas else [('id', '=', False)]
            # else:
            record.domain_location_general_id = [('id', '=', False)]

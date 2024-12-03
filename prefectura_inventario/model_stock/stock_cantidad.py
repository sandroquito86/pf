from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('manzana_context'):
            args = args or []
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            
            if es_coordinador and user.programa_id:
                args = [('location_id.programa_id', '=', user.programa_id.id)] + args
            elif es_sistema:
                programas = self.env['pf.programas'].search([
                    ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
                ])
                if programas:
                    args = [('location_id.programa_id', 'in', programas.ids)] + args
                else:
                    args = [('id', '=', False)]
                    
        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
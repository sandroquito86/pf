from odoo import models, fields, api

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'   
  

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa_tipo_operacion'):
            args = args if args else []
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')

            if es_coordinador:
                programa_id = user.programa_id.id if user.programa_id else False
                if programa_id:
                    args = [('programa_id', '=', programa_id)] + args
                else:
                    args = [('id', '=', False)]
            elif es_sistema:
                programas = self.env['pf.programas'].search([
                    ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
                ])
                if programas:
                    args = [('programa_id', 'in', programas.ids)] + args
                else:
                    args = [('id', '=', False)]
        
        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
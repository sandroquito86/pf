from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'



    domain_programa_id = fields.Char(string='Domain Programa',compute='_compute_domain_programas')

    @api.depends('code')
    def _compute_domain_programas(self):
        for record in self:
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')

            if es_coordinador:
                # Si es coordinador, solo ve su programa
                if user.programa_id:
                    record.domain_programa_id = [('id', '=', user.programa_id.id)]
                else:
                    record.domain_programa_id = [('id', '=', False)]
            elif es_sistema:
                # Si es sistema, ve todos los programas del módulo 2
                programas = self.env['pf.programas'].search([
                    ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
                ])
                record.domain_programa_id = [('id', 'in', programas.ids)] if programas else [('id', '=', False)]
            else:
                # Para otros usuarios, no ven ningún programa
                record.domain_programa_id = [('id', '=', False)]

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa_almacen'):
            args = args if args else []
            user = self.env.user

            # Verificar si el usuario es coordinador
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')

            if es_coordinador:
                # Coordinador solo ve almacenes de su programa
                programa_id = user.programa_id.id if user.programa_id else False
                if programa_id:
                    args = [('programa_id', '=', programa_id)] + args
                else:
                    args = [('id', '=', False)]  # No muestra nada si no tiene programa asignado
            elif es_sistema:
                # Sistema ve almacenes de programas con modulo_id = 2
                args = [('programa_id.modulo_id', '=', 2)] + args

        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
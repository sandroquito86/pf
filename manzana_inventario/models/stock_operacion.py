from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    domain_location_id = fields.Char(string='Domain Location Source', compute='_compute_domain_location')
    domain_location_dest_id = fields.Char(string='Domain Location Dest', compute='_compute_domain_location_dest')

    @api.depends('picking_type_id')
    def _compute_domain_location(self):
        for record in self:
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            if es_coordinador:
                if user.programa_id:
                    # Solo ubicaciones de su programa
                    record.domain_location_id = str([('programa_id', '=', self.env.user.programa_id.id)])
                else:
                    record.domain_location_id = str([('id', '=', False)])
            elif es_sistema:
                # Todas las ubicaciones de programas del módulo 2
                programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)])
                if programas:
                    record.domain_location_id = str([('programa_id', 'in', programas.ids)])
                else:
                    record.domain_location_id = str([('id', '=', False)])
            else:
                record.domain_location_id = str([('id', '=', False)])

    @api.depends('picking_type_id')
    def _compute_domain_location_dest(self):
        for record in self:
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            # Buscar programas del módulo 2
            programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)])

            if es_coordinador or es_sistema:
                if programas:
                    # Tanto coordinador como sistema pueden enviar a cualquier ubicación de programas del módulo 2
                    record.domain_location_dest_id = str([('programa_id', 'in', programas.ids)])
                else:
                    record.domain_location_dest_id = str([('id', '=', False)])
            else:
                record.domain_location_dest_id = str([('id', '=', False)])

    

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa_picking'):
            args = args or []
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')

            picking_types = self.env['stock.picking.type'].search([('code', '=', 'incoming')])
            location_vendor = self.env.ref('stock.stock_location_suppliers')

            domain = []
            if es_coordinador and user.programa_id:
                domain = ['|', '|',
                    ('location_id', '=', location_vendor.id),
                    ('location_id.programa_id', '=', user.programa_id.id),
                    ('location_dest_id.programa_id', '=', user.programa_id.id)
                ]
            elif es_sistema:
                programas = self.env['pf.programas'].search([
                    ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
                ])
                if programas:
                    domain = ['|', '|',
                        ('location_id', '=', location_vendor.id),
                        ('location_id.programa_id', 'in', programas.ids),
                        ('location_dest_id.programa_id', 'in', programas.ids)
                    ]

            if domain:
                args = domain + args

        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
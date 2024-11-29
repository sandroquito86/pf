from odoo import models, fields, api

class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    visible_en_programa = fields.Boolean(string='Visible en Programa', compute='_compute_visible_en_programa',store=True)
    domain_location_id = fields.Char(string='Domain Location', compute='_compute_domain_location')

    @api.depends('warehouse_id')
    def _compute_domain_location(self):
        for record in self:
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            if es_coordinador:
                if user.programa_id:
                    # Solo ve ubicaciones de su programa
                    record.domain_location_id = [('programa_id', '=', user.programa_id.id)]
                else:
                    record.domain_location_id = [('id', '=', False)]
            elif es_sistema:
                # Si hay almacén seleccionado, filtra por ese almacén
                if record.warehouse_id:
                    record.domain_location_id = [
                        ('warehouse_id', '=', record.warehouse_id.id),
                        ('programa_id', '!=', False)
                    ]
                else:
                    programas = self.env['pf.programas'].search([
                        ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
                    ])
                    record.domain_location_id = [
                        ('programa_id', 'in', programas.ids)
                    ] if programas else [('id', '=', False)]
            else:
                record.domain_location_id = [('id', '=', False)]

    @api.depends('programa_id',"usage")
    def _compute_visible_en_programa(self):
        for record in self:
            record.visible_en_programa = bool(record.programa_id)

    

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
            if self._context.get('filtrar_programa_ubicacion'):
                args = args if args else []
                user = self.env.user
                es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
                es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
                if es_coordinador:
                    programa_id = user.programa_id.id if user.programa_id else False
                    if programa_id:
                        args = ['|', ('location_id', '=', False), ('programa_id', '=', programa_id)] + args
                    else:
                        args = [('id', '=', False)]
                elif es_sistema:
                    programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)])
                    if programas:
                        # Incluimos las ubicaciones padre y las que coinciden con el criterio
                        args = [
                            '|',
                            ('location_id', '=', False),  # Incluir ubicaciones padre
                            ('programa_id', 'in', programas.ids)
                        ] + args
                    else:
                        args = [('id', '=', False)]
            return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
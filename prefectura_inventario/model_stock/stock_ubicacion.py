from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', related='warehouse_id.programa_id', store=True)
    visible_en_programa = fields.Boolean(string='Visible en Programa', compute='_compute_visible_en_programa',store=True)
    domain_location_id = fields.Char(string='Domain Location', compute='_compute_domain_location')

    @api.depends('warehouse_id')
    def _compute_domain_location(self):
        for record in self:
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            es_stock_manager = user.has_group('stock.group_stock_manager')

            if es_stock_manager:
                # Stock manager ve todas las ubicaciones
                if record.warehouse_id:
                    record.domain_location_id = [('warehouse_id', '=', record.warehouse_id.id)]
                else:
                    # Excluir ubicaciones virtuales y de partners
                    virtual_loc = self.env.ref('stock.stock_location_locations_virtual', False)
                    partner_loc = self.env.ref('stock.stock_location_locations_partner', False)
                    
                    excluir_ids = []
                    if virtual_loc:
                        excluir_ids.append(virtual_loc.id)
                    if partner_loc:
                        excluir_ids.append(partner_loc.id)
                        
                    record.domain_location_id = [
                        ('location_id', 'not in', excluir_ids),
                        ('location_id.location_id', 'not in', excluir_ids)
                    ]
            elif es_coordinador:
                if user.programa_id:
                    record.domain_location_id = [('programa_id', '=', user.programa_id.id)]
                else:
                    record.domain_location_id = [('id', '=', False)]
            elif es_sistema:
                if record.warehouse_id:
                    record.domain_location_id = [
                        ('warehouse_id', '=', record.warehouse_id.id),
                        ('programa_id', '!=', False)
                    ]
                else:
                    programas = self.env['pf.programas'].search([
                        ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
                    ])
                    record.domain_location_id = [('programa_id', 'in', programas.ids)] if programas else [('id', '=', False)]
            else:
                record.domain_location_id = [('id', '=', False)]

    @api.depends('programa_id',"usage")
    def _compute_visible_en_programa(self):
        for record in self:
            record.visible_en_programa = bool(record.programa_id)

    

    # def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
    #     if self._context.get('filtrar_programa_ubicacion'):
    #         args = args if args else []
    #         user = self.env.user
    #         es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
    #         es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
    #         es_stock_manager = user.has_group('stock.group_stock_manager')

    #         if es_stock_manager:
    #             # Stock manager ve todas las ubicaciones y sus padres
    #             args = ['|', ('location_id', '=', False), ('id', '!=', False)] + args
    #         elif es_coordinador:
    #             programa_id = user.programa_id.id if user.programa_id else False
    #             if programa_id:
    #                 args = ['|', ('location_id', '=', False), ('programa_id', '=', programa_id)] + args
    #             else:
    #                 args = [('id', '=', False)]
    #         elif es_sistema:
    #             programas = self.env['pf.programas'].search([
    #                 ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
    #             ])
    #             if programas:
    #                 # Incluimos las ubicaciones padre y las que coinciden con el criterio
    #                 args = [
    #                     '|',
    #                     ('location_id', '=', False),  # Incluir ubicaciones padre
    #                     ('programa_id', 'in', programas.ids)
    #                 ] + args
    #             else:
    #                 args = [('id', '=', False)]
    #         else:
    #             args = [('id', '=', False)]

    #     return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa_ubicacion'):
            args = args if args else []
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            es_stock_manager = user.has_group('stock.group_stock_manager')
            
            es_contexto_manzana = self._context.get('manzana_context', False)
            
            if es_stock_manager and not es_contexto_manzana:
                # Excluir ubicaciones virtuales y de partners usando búsqueda directa
                virtual_loc = self.env.ref('stock.stock_location_locations_virtual', False)
                partner_loc = self.env.ref('stock.stock_location_locations_partner', False)
                excluir_ids = []                
                if virtual_loc:
                    self.env.cr.execute("""
                        WITH RECURSIVE location_tree AS (
                            SELECT id FROM stock_location WHERE id = %s
                            UNION
                            SELECT sl.id FROM stock_location sl
                            INNER JOIN location_tree lt ON lt.id = sl.location_id
                        )
                        SELECT id FROM location_tree
                    """, (virtual_loc.id,))
                    excluir_ids.extend([r[0] for r in self.env.cr.fetchall()])
                
                if partner_loc:
                    self.env.cr.execute("""
                        WITH RECURSIVE location_tree AS (
                            SELECT id FROM stock_location WHERE id = %s
                            UNION
                            SELECT sl.id FROM stock_location sl
                            INNER JOIN location_tree lt ON lt.id = sl.location_id
                        )
                        SELECT id FROM location_tree
                    """, (partner_loc.id,))
                    excluir_ids.extend([r[0] for r in self.env.cr.fetchall()])
                
                if excluir_ids:
                    args = [('id', 'not in', excluir_ids)] + args
                    
            elif es_coordinador:
                if es_contexto_manzana:
                    programa_id = user.programa_id.id if user.programa_id else False
                    if programa_id:
                        self.env.cr.execute("""
                            WITH RECURSIVE location_hierarchy AS (
                                -- Ubicaciones base del programa
                                SELECT id, location_id
                                FROM stock_location
                                WHERE programa_id = %s
                                UNION
                                -- Ubicaciones padre
                                SELECT sl.id, sl.location_id
                                FROM stock_location sl
                                INNER JOIN location_hierarchy lh ON sl.id = lh.location_id
                            )
                            SELECT id FROM location_hierarchy
                        """, (programa_id,))
                        
                        ubicaciones_ids = [r[0] for r in self.env.cr.fetchall()]
                        if ubicaciones_ids:
                            args = [('id', 'in', ubicaciones_ids)] + args
                        else:
                            args = [('id', '=', False)]
                    else:
                        args = [('id', '=', False)]
            elif es_sistema:
                if es_contexto_manzana:
                    modulo_2 = self.env.ref('prefectura_base.modulo_2').id
                    self.env.cr.execute("""
                        WITH RECURSIVE location_hierarchy AS (
                            -- Ubicaciones base del módulo
                            SELECT sl.id, sl.location_id
                            FROM stock_location sl
                            JOIN stock_warehouse sw ON sl.warehouse_id = sw.id
                            JOIN pf_programas pp ON sw.programa_id = pp.id
                            WHERE pp.modulo_id = %s
                            UNION
                            -- Ubicaciones padre
                            SELECT sl.id, sl.location_id
                            FROM stock_location sl
                            INNER JOIN location_hierarchy lh ON sl.id = lh.location_id
                        )
                        SELECT id FROM location_hierarchy
                    """, (modulo_2,))
                    
                    ubicaciones_ids = [r[0] for r in self.env.cr.fetchall()]
                    if ubicaciones_ids:
                        args = [('id', 'in', ubicaciones_ids)] + args
                    else:
                        args = [('id', '=', False)]

        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
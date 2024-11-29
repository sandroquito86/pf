# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta
from random import randint
from datetime import datetime
from odoo.exceptions import UserError
import pytz
from datetime import timedelta
from babel.dates import format_date


class MzServicioVeterinario(models.Model):
    _name = 'mz.servicio.veterinario'
    _description = 'Servicios Veterinarios'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, hora_inicio desc'
    _rec_name = 'codigo'

    @api.model
    def _get_tipo_servicio_domain(self):
        catalogo_id = self.env.ref('prefectura_base.catalogo_tipos_servicio_veterinario').id
        return [('catalogo_id', '=', catalogo_id)]

    # Campos de identificación y control
    codigo = fields.Char(string='Código', required=True, store=True)

    tipo_servicio_id = fields.Many2one('pf.items', string='Tipo de Servicio', domain=_get_tipo_servicio_domain, tracking=True)

    # Campos relacionales
    beneficiario_id = fields.Many2one('mz.beneficiario', string='Propietario', required=True, tracking=True)
    mascota_id = fields.Many2one('mz.mascota', string='Mascota', required=True, domain="[('beneficiario_id', '=', beneficiario_id)]", tracking=True)
    veterinario_id = fields.Many2one('hr.employee', string='Veterinario', required=True, tracking=True)
    programa_id = fields.Many2one('pf.programas', string='Programa', required=True)
    fecha = fields.Date(string='Fecha', required=True, default=fields.Date.context_today, tracking=True)
    hora_inicio = fields.Float(string='Hora de Inicio', required=True, tracking=True)
    hora_fin = fields.Float(string='Hora de Fin', tracking=True)
    observaciones = fields.Text(string='Observaciones', tracking=True)
    motivo_consulta = fields.Text(string='Motivo de Consulta', required=True, tracking=True)
    sintomas = fields.Text(string='Síntomas', tracking=True)
    temperatura = fields.Float(string='Temperatura (°C)', tracking=True)
    peso_actual = fields.Float(string='Peso Actual (kg)', tracking=True)
    frecuencia_cardiaca = fields.Integer(string='Frecuencia Cardíaca', tracking=True)
    frecuencia_respiratoria = fields.Integer(string='Frecuencia Respiratoria', tracking=True)
    diagnostico = fields.Text(string='Diagnóstico', tracking=True)
    tratamiento = fields.Text(string='Tratamiento Indicado', tracking=True)
    # insumo_ids = fields.One2many('mz.servicio.veterinario.insumo', 'servicio_id', string='Insumos Utilizados')
    state = fields.Selection([('borrador', 'Borrador'), ('en_curso', 'En Curso'), ('finalizado', 'Finalizado')], string='Estado', default='borrador', tracking=True)
    receta_ids = fields.One2many('mz.receta.veterinaria.linea', 'servicio_veterinario_id', string='Receta de Medicamentos')
    picking_id = fields.Many2one('stock.picking', string='Orden de Entrega', readonly=True)

    @api.constrains('codigo')
    def _check_codigo(self):
        for record in self:
            if record.codigo:
                codigo_existente = self.search([
                    ('codigo', '=', record.codigo),
                    ('id', '!=', record.id)
                ], limit=1)
                if codigo_existente:
                    raise UserError('Ya existe una servico veterinario con el mismo código.')
                

    @api.constrains('hora_inicio', 'hora_fin')
    def _check_horas(self):
        for record in self:
            if record.hora_fin and record.hora_inicio > record.hora_fin:
                raise UserError('La hora de fin debe ser posterior a la hora de inicio.')
            if (record.hora_inicio < 0 or record.hora_inicio >= 24) or \
               (record.hora_fin and (record.hora_fin < 0 or record.hora_fin >= 24)):
                raise UserError('Las horas deben estar entre 00:00 y 23:59.')


    @api.onchange('fecha')
    def _onchange_hora_inicio(self):
        for record in self:
            user_tz = self.env.user.tz or 'UTC'  # Obtiene la zona horaria del usuario o usa 'UTC' por defecto
            local_tz = pytz.timezone(user_tz)
            ahora = datetime.now(pytz.utc).astimezone(local_tz)  # Convierte la hora actual a la zona horaria del usuario
            record.hora_inicio = ahora.hour + ahora.minute / 60.0

    def action_iniciar(self):
        self.ensure_one()
        if not self.hora_inicio:
            raise UserError('Debe registrar la hora de inicio antes de comenzar.')
        self.write({'state': 'en_curso'})

    def action_finalizar(self):
        self.ensure_one()
        if not self.hora_fin:
            raise UserError('Debe registrar la hora de fin antes de finalizar.')
        self.write({'state': 'finalizado'})


    def generar_orden_entrega(self):
        self.ensure_one()
        
        if self.picking_id:
            raise UserError('Ya existe una orden de entrega para esta consulta.')
        
        productos_en_stock = self.receta_ids.filtered(lambda r: r.en_inventario)
        
        if productos_en_stock:
            # Buscar el tipo de operación para salidas
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'outgoing'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            
            if not picking_type:
                raise UserError('No se encontró un tipo de operación para salida de inventario.')
            
            # Verificar que las ubicaciones existan
            if not picking_type.default_location_src_id or not picking_type.default_location_dest_id:
                raise UserError('Las ubicaciones origen y destino no están configuradas en el tipo de operación.')
            
            # Asegurarse que el partner_id sea válido
            if not self.beneficiario_id.user_id.partner_id:
                raise UserError('El beneficiario no tiene un contacto asociado.')
            
            valores_picking = {
                'partner_id': self.beneficiario_id.user_id.partner_id.id,
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'origin': f'Consulta {self.codigo}',
                'company_id': self.env.company.id,
                'scheduled_date': fields.Datetime.now(),
                'move_type': 'direct',  # Entrega directa
                'state': 'draft',
            }
            
            # Crear el picking
            picking = self.env['stock.picking'].create(valores_picking)
            
            # Crear los movimientos de stock
            for linea in productos_en_stock:
                move_vals = {
                    'name': linea.producto_id.name,
                    'product_id': linea.producto_id.id,
                    'product_uom_qty': linea.cantidad,
                    'product_uom': linea.producto_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'company_id': self.env.company.id,
                    'state': 'draft',
                    'picking_type_id': picking_type.id,
                }
                self.env['stock.move'].create(move_vals)
            
            self.picking_id = picking.id
            return True
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Información',
                    'message': 'No se generó orden de entrega ya que no hay productos en stock.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
    @api.model
    def create(self, vals):
        servicio = super(MzServicioVeterinario, self).create(vals)
        # Actualizar el peso de la mascota
        if servicio.peso_actual:
            servicio.mascota_id.write({'peso': servicio.peso_actual})
        if 'codigo' in vals:
            self.env['mz.asistencia_servicio'].search([
                ('codigo', '=', vals['codigo'])
            ]).write({
                'atendido': True,
                'servicio_veterinario_id': servicio.id
            })
        else:
            raise UserError('No se ha generado el código.')
        return servicio
    

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar turnos cuando viene el contexto
        """
        args = args or []
        user = self.env.user
        
        # Evitar recursión usando un contexto especial
        if not self._context.get('disable_custom_search'):
            if self._context.get('filtrar_programa'):                   
                # Verificar grupos
                if user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
                    # Para coordinador: ver solo programas de módulo 2
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id.modulo_id', '=', 2)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                elif user.has_group('manzana_de_cuidados.group_mz_registro_informacion') or \
                    user.has_group('manzana_de_cuidados.group_coordinador_manzana') or \
                    user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id', '=', user.programa_id.id),
                        ('state', '=', 'finalizado')
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                elif user.has_group('manzana_de_cuidados.group_mz_prestador_servicio'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    if_veterinari = False
                    for servicio in user.employee_id.servicios_ids:
                        if servicio.servicio_id.tipo_servicio == 'mascota':
                            if_veterinari = True
                            break
                    if if_veterinari:
                        programa_ids = self.with_context(disable_custom_search=True).search([
                                        ('programa_id', '=', user.programa_id.id)
                                    ]).ids
                        base_args = [('id', 'in', programa_ids)]
                    else:
                        base_args = [('id', 'in', [])]
                else :
                    # Para usuarios sin rol especial: ver solo sus propios programas
                    base_args = [('id', 'in', [])]

                args = base_args + args

        return super(MzServicioVeterinario, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
    

    def get_appropriate_view(self):
        # Obtener el usuario actual
        user = self.env.user
        
        # Definir vistas por defecto (limitadas)
        tree_view = self.env.ref('manzana_de_cuidados.view_mz_servicio_veterinario_tree').id
        form_view = self.env.ref('manzana_de_cuidados.view_mz_servicio_veterinario_form_read').id
        
        # Verificar si el usuario tiene permisos específicos
        # if (user.has_group('manzana_de_cuidados.group_mz_prestador_servicio') or \
        #     user.has_group('manzana_de_cuidados.group_beneficiario_manager')):
        #     # Vistas completas para usuarios con permisos
        #     tree_view = self.env.ref('manzana_de_cuidados.view_mz_asesoria_legal_tree').id
        #     form_view = self.env.ref('manzana_de_cuidados.view_mz_asesoria_legal_form_read').id
        
        # Preparar la acción de ventana
        action = {
            'name': 'Servicio Veterinario',
            'type': 'ir.actions.act_window',
            'res_model': 'mz.servicio.veterinario',
            'view_mode': 'tree,form',
            'views': [
                (tree_view, 'tree'),
                (form_view, 'form')
            ],
            'context': {
                'default_modulo_id': 2,
                'filtrar_programa': True
            },
            'target': 'current'
        }
        
        return action
    

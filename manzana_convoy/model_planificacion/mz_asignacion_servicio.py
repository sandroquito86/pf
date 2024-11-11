# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from string import ascii_letters, digits
import string


class AsignarServicio(models.Model):
    _inherit = 'mz.asignacion.servicio'   

    convoy_id = fields.Many2one('mz.convoy', string='Convoy', required=True, tracking=True)
    domain_convoy_id = fields.Char(string='Domain Convoy',compute='_compute_domain_convoy')    
    numero_turnos = fields.Integer(string='Cantidad de turnos',)
    planificacion_ids = fields.One2many('mz.planificacion.servicio', 'asignacion_id', string='Turnos')

    # def action_generar_turnos(self):
    #     self.ensure_one()
    #     # Eliminamos turnos existentes si los hay
    #     self.planificacion_ids.unlink()
        
    #     # Generamos los nuevos turnos
    #     turnos_list = []
    #     for i in range(self.numero_turnos):
    #         vals = {
    #             'asignacion_id': self.id,
    #             'fecha': fields.Date.today(),
    #             'estado': 'activo',               
    #             'maximo_beneficiarios': 1,
    #         }
    #         turnos_list.append((0, 0, vals))
        
    #     self.write({'planificacion_ids': turnos_list})

       
    
    @api.depends('servicio_id')
    def _compute_domain_convoy(self):
        for record in self:
            # Buscar los convoy en estado aprobado
            convoys_aprobados = self.env['mz.convoy'].search([
                ('state', '=', 'aprobado')
            ])
            if convoys_aprobados:
                record.domain_convoy_id = [('id', 'in', convoys_aprobados.ids)]
            else:
                record.domain_convoy_id = [('id', 'in', [])]

    @api.onchange('convoy_id')
    def _onchange_convoy_id(self):        
        if self.convoy_id:
            self.programa_id = self.convoy_id.programa_id
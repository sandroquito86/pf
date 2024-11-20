# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from datetime import timedelta
from babel.dates import format_date


class AgendarServicio(models.Model):
    _inherit = 'mz.agendar_servicio'
    
    

    convoy_id = fields.Many2one('mz.convoy', string='Convoy', required=True, tracking=True)
    convoy_id_domain = fields.Char(compute="_compute_programa_convoy_id_domain", readonly=True, store=False, )

    @api.depends('convoy_id')
    def _compute_programa_convoy_id_domain(self):
      for record in self:         
        convoy_ids = record.convoy_id.search([('state','=','aprobado')]).ids
        record.convoy_id_domain = [('id', 'in', convoy_ids)]    

    
    @api.onchange('convoy_id')
    def _onchange_field(self):
        for record in self:
            if(record.convoy_id):
                record.programa_id = record.convoy_id.programa_id
    
    
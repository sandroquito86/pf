# -*- coding: utf-8 -*-
from ast import Store
import json
import logging
import time
from datetime import date, datetime, timedelta

import requests
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_date, is_html_empty




class MzElearning(models.Model):
    _inherit = 'slide.channel'
    _description = 'E-learning de Manzana de Cuidados'


    @api.model
    def _get_tipo_dependiente_domain(self):
        catalogo_id = self.env.ref('manzana_elearning.capacitacion_curso_charla').id
        return [('catalogo_id', '=', catalogo_id)]

    name = fields.Char('Name', translate=True, required=False, compute='_compute_name', store=True)
    course_item = fields.Many2one('pf.items', string="Capacitación", required=True, ondelete="cascade", domain=_get_tipo_dependiente_domain , tracking=True)
    assignments_ids = fields.One2many('mz.elearning.assignments', 'course_id')
    # programas_ids = fields.One2many('mz.elearning.programs', 'course_id')
    is_async_mode = fields.Boolean(string="Modo Asincrónico", tracking=False)


    @api.depends('course_item')
    def _compute_name(self):
        for record in self:
            record.name = f'{record.course_item.name}' if record.course_item.name else ''
            

    def action_view_attendances_student(self):
        action = self.env["ir.actions.actions"]._for_xml_id("manzana_elearning.slide_channel_partner_offline_action")
        action['domain'] = [('course_id', 'in', self.ids)]
        return action



class ChannelBeneficiaryRelation(models.Model):
    _inherit = 'slide.channel.partner'
    _description = 'Beneficiarios/Partners Cursos'


    partner_id = fields.Many2one('res.partner', index=True, required=True, ondelete='cascade')
    student_id = fields.Many2one('mz.beneficiario', compute="_compute_student_id", store=True)
    # completion_attendance = fields.Integer('% Completed Contents', default=0, group_operator="avg")
    
    
    @api.depends('partner_id')
    def _compute_student_id(self):
        for rec in self:
            if rec.partner_id:
                user = self.env['res.users'].sudo().search([('partner_id', '=', rec.partner_id.id)])
                beneficiary = self.env['mz.beneficiario'].sudo().search([('user_id', '=', user.id)])
                rec.student_id = beneficiary.id
            else:
                rec.student_id = False


class MzElearningSlide(models.Model):
    _inherit = 'slide.slide'
    _description = 'Sección de contenidos'


    @api.model_create_multi
    def create(self, vals_list):
        # Modificar is_published y mantener la lógica de date_published
        for vals in vals_list:
            vals['is_published'] = True
            if not vals.get('date_published'):
                vals['date_published'] = datetime.now()
        
        slides = super().create(vals_list)
        return slides



    





    

    

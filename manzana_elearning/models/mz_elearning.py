# -*- coding: utf-8 -*-
import json
import logging
import time
from datetime import date, datetime, timedelta

import requests
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_date




class MzElearning(models.Model):
    _inherit = 'slide.channel'
    _description = 'E-learning de Manzana de Cuidados'

    assignments_ids = fields.One2many('mz.elearning.assignments', 'course_id')


    def action_view_attendances_student(self):
        action = self.env["ir.actions.actions"]._for_xml_id("manzana_elearning.attendance_student_action")
        action['domain'] = [('course_id', 'in', self.ids)]
        return action



class ChannelBeneficiaryRelation(models.Model):
    _inherit = 'slide.channel.partner'
    _description = 'Beneficiarios/Partners Cursos'

    partner_id = fields.Many2one('res.partner', index=True, required=True, ondelete='cascade')
    student_id = fields.Many2one('mz.beneficiario', compute="_compute_student_id", store=True)

    @api.depends('partner_id')
    def _compute_student_id(self):
        for rec in self:
            if rec.partner_id:
                user = self.env['res.users'].sudo().search([('partner_id', '=', rec.partner_id.id)])
                beneficiary = self.env['mz.beneficiario'].sudo().search([('user_id', '=', user.id)])
                rec.student_id = beneficiary.id
            else:
                rec.student_id = False





    

    

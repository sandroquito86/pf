# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import random
import uuid
from collections import defaultdict

import werkzeug

from odoo import api, exceptions, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import is_html_empty


class Survey(models.Model):
    _inherit = 'survey.survey'
    _description = 'Certificados de capacitaciones de E-learning de Manzana de Cuidados'



    attendance_success_min = fields.Float('Asistencia mínima requerida (%)', default=80.0)
    on_site_training = fields.Boolean("Capacitación Presencial")


    _sql_constraints = [
        ('access_token_unique', 'unique(access_token)', 'Access token should be unique'),
        ('session_code_unique', 'unique(session_code)', 'Session code should be unique'),
        ('certification_check', "CHECK( certification=False )",
            'You can only create certifications for surveys that have a scoring mechanism.'),
        ('scoring_success_min_check', "CHECK( scoring_success_min IS NULL OR (scoring_success_min>=0 AND scoring_success_min<=100) )",
            'The percentage of success has to be defined between 0 and 100.'),
        ('time_limit_check', "CHECK( (is_time_limited=False) OR (time_limit is not null AND time_limit > 0) )",
            'The time limit needs to be a positive number if the survey is time limited.'),
        ('attempts_limit_check', "CHECK( (is_attempts_limited=False) OR (attempts_limit is not null AND attempts_limit > 0) )",
            'The attempts limit needs to be a positive number if the survey has a limited number of attempts.'),
        ('badge_uniq', 'unique (certification_badge_id)', "The badge for each survey should be unique!"),
    ]



    @api.model_create_multi
    def create(self, vals_list):
        # Modificar is_published y mantener la lógica de date_published
        for vals in vals_list:
            if vals.get('on_site_training'):
                vals['certification'] = True
                vals['scoring_type'] = 'no_scoring'
        
        survey = super().create(vals_list)
        return survey


    
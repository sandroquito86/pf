# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pytz

from collections import defaultdict
from datetime import datetime, timedelta
from operator import itemgetter
from pytz import timezone

from odoo import models, fields, api, exceptions, _
from odoo.addons.resource.models.utils import Intervals
from odoo.tools import format_datetime
from odoo.osv.expression import AND, OR
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError
from odoo.tools import format_duration

# def get_google_maps_url(latitude, longitude):
#     return "https://maps.google.com?q=%s,%s" % (latitude, longitude)


class MzAttendanceStudent(models.Model):
    _name = "mz.attendance.student"
    _description = "Attendance Student"
    _order = "check_in desc"
    _inherit = "mail.thread"


from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class StudentAttendance(models.Model):
    _name = 'mz.attendance.student'
    _description = 'Asistencia de Estudiantes'
    _rec_name = 'student_id'

    student_id = fields.Many2one('mz.beneficiario', string='Beneficiario', required=True)
    course_id = fields.Many2one('slide.channel', string='Curso', required=True)
    date = fields.Date(string='Fecha', required=True)
    state = fields.Selection([
        ('present', 'Asistió'),
        ('absent', 'No Asistió')
    ], string='Asistencia', required=True)

    sub_state = fields.Selection([
        ('na', 'N/A'),
        ('jst', 'Falta Justificada'),
        ('wjst', 'Falta No Justificada')
    ], string='Estado', required=True)
    
    _sql_constraints = [
        ('unique_attendance',
         'UNIQUE(student_id, course_id, date)',
         'Ya existe un registro de asistencia para este estudiante en este curso y fecha.')
    ]

    @api.constrains('date')
    def _check_date(self):
        for record in self:
            if record.date > fields.Date.today():
                raise ValidationError("No se pueden registrar asistencias para fechas futuras.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            existing = self.search([
                ('student_id', '=', vals.get('student_id')),
                ('course_id', '=', vals.get('course_id')),
                ('date', '=', vals.get('date'))
            ])
            if existing:
                raise ValidationError("Ya existe un registro de asistencia para este estudiante en este curso y fecha.")
        
        return super().create(vals_list)


    def unlink(self):
        res = super().unlink()
        return res


    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise exceptions.UserError(_('You cannot duplicate an attendance.'))

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class MzStudentAttendance(models.Model):
    _name = 'mz.attendance.student'
    _description = 'Asistencia de Estudiantes'
    _rec_name = 'student_id'

    student_id = fields.Many2one('mz.beneficiario', string='Beneficiario', required=True)
    agenda_id = fields.Many2one('mz.agenda.elearning', string='Curso', required=True)
    date = fields.Date(string='Fecha', required=True)
    observations = fields.Char(string="Observaciones")
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
         'UNIQUE(student_id, agenda_id, date)',
         'Ya existe un registro de asistencia para este estudiante en este curso y fecha.')
    ]

    def _is_valid_attendance(self, attendance):
        return (attendance.state == 'present' or 
            (attendance.state == 'absent' and attendance.sub_state == 'jst'))

    def _update_overtime_attendance_percentage(self, student_offline_ids, agenda):
        valid_session_dates = agenda.planificacion_ids.mapped('date')
        if not valid_session_dates:
            return False
            
        for participant in student_offline_ids:
            attendances = self.env['mz.attendance.student'].search([
                ('student_id', '=', participant.beneficiary_id.id),
                ('agenda_id', '=', agenda.id),
                ('date', 'in', valid_session_dates)
            ])
            
            valid_count = len(attendances.filtered(lambda a: self._is_valid_attendance(a)))
            attendance_percentage = (valid_count / len(valid_session_dates)) * 100
            participant.write({'attendance_percentage': attendance_percentage})
        
        return True


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            existing = self.search([
                ('student_id', '=', vals.get('student_id')),
                ('agenda_id', '=', vals.get('agenda_id')),
                ('date', '=', vals.get('date'))
            ])
            if existing:
                raise ValidationError("Ya existe un registro de asistencia para este estudiante en este curso y fecha.")
                
        records = super().create(vals_list)
        students = records.mapped('student_id')
        agenda_id = records[0].agenda_id if records else False  # Más seguro que usar [0]
        
        student_offline_ids = self.env['mz.slide.channel.partner.offline'].sudo().search([
            ('beneficiary_id', 'in', students.ids),
            ('agenda_id', '=', agenda_id.id)  # Agregar filtro por agenda
        ])

        if student_offline_ids and agenda_id:
            self._update_overtime_attendance_percentage(student_offline_ids, agenda_id)
        return records


    def unlink(self):
        res = super().unlink()
        return res


    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise exceptions.UserError(_('You cannot duplicate an attendance.'))


    def action_open_beneficiary(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Beneficiario',
            'res_model': 'mz.beneficiario',
            'view_mode': 'form',
            'res_id': self.student_id.id,
            'target': 'new',
            'views': [(self.env.ref('manzana_de_cuidados.mz_beneficiario_view_form_limit').id, 'form')],
            'context': {'form_view_initial_mode': 'readonly'},
        }

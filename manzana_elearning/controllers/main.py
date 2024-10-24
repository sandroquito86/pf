# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import request
from datetime import datetime, time, timedelta, time
from functools import reduce
import base64
import json
import logging
import traceback

_logger = logging.getLogger(__name__)




class ManzanaElearning(http.Controller):
    @http.route('/manzana_beneficiary/attendees', type='json', auth='user', methods=['POST'])
    def manzana_beneficiary_attendees(self, slideChanel):
        attendees = request.env['slide.channel.partner'].sudo().search([('channel_id', '=', int(slideChanel))])
        course_attendees = []
        for attendee in attendees:
            course_attendees.append({
            'id': attendee.id,
            'student_id': attendee.student_id.id,
            'name': attendee.partner_id.name,
            'attendance': True,
            'absent': False,
            'justified': False
        })


        return json.dumps({
            'course_attendees': course_attendees
        })



    @http.route(['/submit/assignment/<int:assignment_id>'], type='http', auth="user", website=True, methods=['POST'], csrf=False)
    def submit_assignment(self, assignment_id, user_id, **post):
        try:
            submitted_file = request.httprequest.files.get('submitted_file')
            if not submitted_file:
                return json.dumps({'error': 'No existe archivo'})

            if not user_id:
                return json.dumps({'error': 'No existe usuario'})

            assignment = request.env['mz.elearning.assignments'].sudo().browse(assignment_id)
            student = request.env['pf.beneficiario'].sudo().search([('user_id','=',int(user_id))])

            # Buscar si ya existe una tarea subida para este estudiante
            existing_assignment = request.env['mz.student.assignments'].sudo().search([
                ('assignment_id', '=', assignment_id),
                ('student_id', '=', student.id)
            ], limit=1)

            if existing_assignment:
                return json.dumps({'error': 'Error al cargar el archivo.'})

            values = {
                'name': f"{assignment.name}",
                'assignment_id': assignment_id,
                'student_id': student.id,
                'submitted_file': base64.b64encode(submitted_file.read()),
                'submitted_filename': submitted_file.filename,
                'status': 'submitted',
            }

            student_assignment = request.env['mz.student.assignments'].sudo().create(values)
            assignment_values = [ {'id': st.id, 'filename': st.submitted_filename} for st in student_assignment]

            return json.dumps({'success': True, 'assignment': assignment_values})
        except Exception as e:
            return json.dumps({'error': str(e)})


    @http.route('/delete/assignment/<int:student_assignment_id>', type='http', auth="user", website=True, csrf=True)
    def delete_assignment(self, student_assignment_id, **post):
        try:
            student_assignment = request.env['mz.student.assignments'].sudo().browse(int(student_assignment_id))
            # if student_assignment and student_assignment.student_id.id == request.env.user.id:
            if student_assignment:
                student_assignment.unlink()
                return json.dumps({'success': True})
            else:
                return json.dumps({'success': False, 'error': 'No se encontró la tarea o no tienes permiso para eliminarla'})
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
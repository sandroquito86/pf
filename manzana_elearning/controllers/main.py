# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import request
from datetime import datetime, time, timedelta, time
from functools import reduce
import base64
import json
import logging
import traceback

from odoo.http import request, content_disposition

_logger = logging.getLogger(__name__)




class ManzanaElearning(http.Controller):
    @http.route('/manzana_beneficiary/attendees', type='json', auth='user', methods=['POST'])
    def manzana_beneficiary_attendees(self, agenda):
        attendees = request.env['mz.slide.channel.partner.offline'].sudo().search([('agenda_id', '=', int(agenda)),('state', '=', 'open')])
        course_attendees = []
        for attendee in attendees:
            course_attendees.append({
            'id': attendee.id,
            'student_id': attendee.beneficiary_id.id,
            'name': attendee.beneficiary_id.name,
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



    def _generate_report(self, user_input, download=True):
        report = request.env["ir.actions.report"].sudo()._render_qweb_pdf('survey.certification_report', [user_input], data={'report_type': 'pdf'})[0]

        report_content_disposition = content_disposition('Certification.pdf')
        if not download:
            content_split = report_content_disposition.split(';')
            content_split[0] = 'inline'
            report_content_disposition = ';'.join(content_split)

        return request.make_response(report, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(report)),
            ('Content-Disposition', report_content_disposition),
        ])


    @http.route(['/certificate/<int:survey_id>/get_certification'], type='http', auth='user', methods=['GET'], website=True)
    def controller_get_certification(self, survey_id, input_id=None, **kwargs):
        survey = request.env['survey.survey'].sudo().search([
            ('id', '=', survey_id),
            ('certification', '=', True)
        ])

        if not survey:
            return request.redirect("/")

        user_input = request.env['survey.user_input'].sudo().browse(int(input_id))

        if not user_input:
            raise UserError(_("El usuario no cuenta con una certificación."))

        return self._generate_report(user_input.id, download=True)
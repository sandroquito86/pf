# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from string import ascii_letters, digits
import string
import datetime

from datetime import timedelta


class ControlAttendance(models.Model):
    _name = 'mz.control.attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Control de asistencias de las capacitaciones'

    
    #name = fields.Char(string='Nombre',  compute='_compute_name', store=True)
    agenda_id = fields.Many2one(string='Agenda', comodel_name='mz.agenda.elearning')
    # total_time = fields.Float(string='Duración del Curso', related='course_id.total_time', digits=(10, 2), store=True)
    start_date = fields.Date(string='Fecha Inicio', related='agenda_id.start_date')
    end_date = fields.Date(string='Fecha Fin', related='agenda_id.end_date')
    # members_applicants_count = fields.Integer('# Postulantes', compute='_compute_applicants_counts') #compute='_compute_members_counts'
    # members_enrolled_count = fields.Integer('# Inscritos', compute='_compute_applicants_counts') #compute='_compute_members_counts'
    # status = fields.Char(string='Estado',  related='agenda_id.state')




    
   
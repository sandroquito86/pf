# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from string import ascii_letters, digits
import string
import datetime

from datetime import timedelta


class AgendaElearning(models.Model):
    _name = 'mz.agenda.elearning'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Agenda para capacitaciones presenciales'

    
    name = fields.Char(string='Nombre',  compute='_compute_name', store=True)
    course_id = fields.Many2one(string='Capacitación', comodel_name='slide.channel', required=True, tracking=True)
    # programs_domain = fields.Char(compute="_compute_programs_domain", readonly=True, store=False)
    programa_id = fields.Many2one('pf.programas', string="Manzana")
    total_time = fields.Float(string='Duración del Curso', related='course_id.total_time', digits=(10, 2), store=True)
    start_date = fields.Date(string='Fecha Inicio', default=lambda self: fields.Date.context_today(self), required=True, help="Día de Inicio de la capacitación")
    end_date = fields.Date(string='Fecha Fin', readonly=True, tracking=True, help="Fecha de finalización de la capacitación")
    members_applicants_count = fields.Integer('# Postulantes', compute='_compute_applicants_counts') #compute='_compute_members_counts'
    members_enrolled_count = fields.Integer('# Inscritos', compute='_compute_applicants_counts') #compute='_compute_members_counts'
    if_certification = fields.Boolean('Certificación?', compute='_compute_certification', store=True, readonly=True)
    certification = fields.Many2one('survey.survey', 'Certificación', compute='_compute_certification', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('planned', 'Planificado'),
        ('in_progress', 'En Progreso'),
        ('done', 'Finalizado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)
    quota_max = fields.Integer(string='Total de Cupos')
    quota_limited = fields.Boolean('Limitar beneficiarios')
    active = fields.Boolean(default=True, string='Activo', tracking=True)   
    detalle_horario_ids = fields.One2many(string='Detalle Horarios', comodel_name='mz.detalle.horarios.elearning', inverse_name='asignacion_horario_id')
    channel_partner_offline_ids = fields.One2many(
        'mz.slide.channel.partner.offline', 'agenda_id', string='Toda la información de postulentes')

    planificacion_ids = fields.One2many(
        string='Planificación de Sesiones',
        comodel_name='mz.planificacion.sesiones',
        inverse_name='horario_id'
    )


    @api.depends('course_id')
    def _compute_certification(self):
        for survey in self:
            if survey.course_id:
                slide_id = self.env['slide.slide'].search([('channel_id','=',survey.course_id.id),('slide_category','=','certification')])
                survey.if_certification = (slide_id)
                survey.certification = slide_id.survey_id.id
            else:
                survey.if_certification = False
                survey.certification = False

    @api.depends('detalle_horario_ids.date')
    def _compute_end_date(self):
        for record in self:
            if record.detalle_horario_ids:
                record.end_date = max(record.detalle_horario_ids.mapped('date'))
            else:
                record.end_date = record.start_date
    
    @api.depends('course_id')
    def _compute_name(self):
        for record in self:
            if record.course_id:
                record.name = f'Agenda de {record.course_id.name}'
                # record.asi_servicio_id = record.servicio_id.servicio_id.id
            else:
                record.name = ''

    def action_redirect_to_applicants(self, action_filter='', status_filter=''):
        action_filter = 'slide_channel_partner_offline_action' if not action_filter else action_filter
        action_ctx = {}
        action = self.env["ir.actions.actions"]._for_xml_id(f"manzana_elearning.{action_filter}")
        if status_filter == 'open':
            action_ctx['search_default_filter_open'] = 1
        
        action_ctx['default_agenda_id'] = self.id
        action['domain'] = [('agenda_id', 'in', self.ids)]
        action['context'] = action_ctx
        return action

    def action_redirect_to_enrolled(self):
        return self.action_redirect_to_applicants('slide_channel_partner_offline_enrolled_action', 'open')

    @api.depends('channel_partner_offline_ids.agenda_id','channel_partner_offline_ids.state')
    def _compute_applicants_counts(self):
        read_group_res = self.env['mz.slide.channel.partner.offline'].sudo()._read_group(
            domain=[('agenda_id', 'in', self.ids)],
            groupby=['agenda_id', 'state'],
            aggregates=['__count']
        )
        data = {(agenda_id.id, state): count for agenda_id, state, count in read_group_res}
        for schedule in self:
            total_count = sum(
                count 
                for (agenda_id, state), count in data.items() 
                if agenda_id == schedule.id
            )
            schedule.members_applicants_count = total_count
            schedule.members_enrolled_count = data.get((schedule.id, 'open'), 0)


    # @api.depends('course_id')
    # def _compute_programs_domain(self):
    #     for record in self:
    #         if record.course_id:
    #             programs = record.course_id.programas_ids.mapped('programa_id')
    #             record.programs_domain = f"[('id', 'in', {programs.ids})]"
    #         else:
    #             record.programs_domain = []


    # _sql_constraints = [('name_unique', 'UNIQUE(course_id)', "Ya existe un horario para esta capacitación / curso.")]
    def action_re_planificacion(self):
        return self.action_crear_planificacion()

    def action_crear_planificacion(self):
        self.ensure_one()
        if not self.detalle_horario_ids:
            raise ValidationError('Debe definir al menos un patrón de horario')

        # Limpiar planificación anterior si existe
        self.planificacion_ids.unlink()
        
        fecha_actual = self.start_date
        fecha_final = ''
        horas_acumuladas = 0
        
        # Diccionario para mapear códigos a números de día de la semana
        dias_semana = {
            '0': 0,  # Lunes
            '1': 1,  # Martes
            '2': 2,  # Miércoles
            '3': 3,  # Jueves
            '4': 4,  # Viernes
            '5': 5,  # Sábado
            '6': 6,  # Domingo
        }

        while horas_acumuladas < self.total_time:
            dia_semana = fecha_actual.weekday()  # 0-6 (Lunes-Domingo)
            
            # Revisar cada patrón de horario
            for detalle in self.detalle_horario_ids:
                # Verificar si este día de la semana está en los días seleccionados
                dias_seleccionados = [dias_semana.get(dia.code, -1) for dia in detalle.days]
                
                if dia_semana in dias_seleccionados:
                    duracion_sesion = detalle.hour_to - detalle.hour_from
                    
                    # Verificar si agregar estas horas excedería el total
                    if horas_acumuladas + duracion_sesion > self.total_time:
                        # Ajustar última sesión
                        horas_pendientes = self.total_time - horas_acumuladas
                        hora_fin_ajustada = detalle.hour_from + horas_pendientes
                        
                        self.env['mz.planificacion.sesiones'].create({
                            'horario_id': self.id,
                            'date': fecha_actual,
                            'hour_from': detalle.hour_from,
                            'hour_to': hora_fin_ajustada,
                        })
                        horas_acumuladas = self.total_time
                        break
                    else:
                        # Crear sesión normal
                        self.env['mz.planificacion.sesiones'].create({
                            'horario_id': self.id,
                            'date': fecha_actual,
                            'hour_from': detalle.hour_from,
                            'hour_to': detalle.hour_to,
                        })
                        horas_acumuladas += duracion_sesion
            
            fecha_actual += timedelta(days=1)
            fecha_final = fecha_actual - timedelta(days=1)

        self.env['mz.control.attendance'].sudo().create({
            'agenda_id': self.id
        })
        self.write({
            'end_date': fecha_final
        })
        return True



class DetalleHorariosElearning(models.Model):
    _name = 'mz.detalle.horarios.elearning'
    _description = 'Detalle de Horarios Elearning'
    _order = 'date, hour_from ASC'
                

    asignacion_horario_id = fields.Many2one(string='Cabecera', comodel_name='mz.agenda.elearning')
    date = fields.Date(string='Fecha', required=True, default=fields.Datetime.now, )
    hour_from = fields.Float(string='Hora Inicio')
    hour_to = fields.Float(string='Hora Fin',)       
    #hora = fields.Char(string='Hora')
    #estado = fields.Boolean(default='True')    
    #observacion = fields.Char(string='Observación')
    #fecha_actualizacion = fields.Date(string='Fecha Actualiza', readonly=True, default=fields.Datetime.now, )
    days = fields.Many2many('training.day', 'schedule_line_day_rel', 'schedule_line_id', 'day_id', string='Días')
    # property_valuation = fields.Selection([
    #     ('manual_periodic', 'Manual'),
    #     ('real_time', 'Automated')], string='Inventory Valuation',
    #     company_dependent=True, copy=True, required=True,
    #     help="""Manual: The accounting entries to value the inventory are not posted automatically.
    #     Automated: An accounting entry is automatically created to value the inventory when a product enters or leaves the company.
    #     """)
    # duracionconsulta = fields.Float(string='Duración del Servicio')

    # _sql_constraints = [('name_unique', 'UNIQUE(asignacion_horario_id,dias)', "No se permiten días repetidos.")]


class PlanificacionSesiones(models.Model):
    _name = 'mz.planificacion.sesiones'
    _description = 'Planificación de Sesiones'
    _order = 'date, hour_from'

    horario_id = fields.Many2one(
        'mz.agenda.elearning',
        string='Horario',
        required=True,
        ondelete='cascade'
    )
    
    date = fields.Date(
        string='Fecha',
        required=True
    )
    
    hour_from = fields.Float(
        string='Hora Inicio',
        required=True
    )
    
    hour_to = fields.Float(
        string='Hora Fin',
        required=True
    )
    
    duration = fields.Float(
        string='Duración (Horas)',
        compute='_compute_duration',
        store=True
    )
    
    # state = fields.Selection([
    #     ('pending', 'Pendiente'),
    #     ('done', 'Realizada'),
    #     ('cancelled', 'Cancelada')
    # ], string='Estado', default='pending')

    @api.depends('hour_from', 'hour_to')
    def _compute_duration(self):
        for record in self:
            record.duration = record.hour_to - record.hour_from


class ChannelUserRelationOffline(models.Model):
    _name = 'mz.slide.channel.partner.offline'
    _description = 'Participantes a capacitaciones presenciales'
    _rec_name = 'beneficiary_id'
    
    agenda_id = fields.Many2one(
        string='Agenda', 
        comodel_name='mz.agenda.elearning',
        required=True
    )
    beneficiary_id = fields.Many2one(
        string='Beneficiario', 
        comodel_name='mz.beneficiario',
        required=True
    )
    is_certifiable = fields.Boolean(
        string='Acreedor a Certificación',
        # compute='_compute_is_certifiable',
        store=True
    )
    state = fields.Selection([
        ('draft', 'En espera'),
        ('open', 'Inscrito'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)
    attendance_ids = fields.One2many(
        'mz.attendance.student',
        'student_id',
        string='Asistencias'
    )
    
    _sql_constraints = [
        ('unique_beneficiary_agenda', 
         'unique(beneficiary_id, agenda_id)',
         'El beneficiario ya está registrado en esta agenda.')
    ]
    
    # @api.depends('attendance_ids.student_id', 'attendance_ids.state')
    # def _compute_participants_count(self):
    #     for record in self:
    #         record.participants_count = self.search_count([
    #             ('agenda_id', '=', record.agenda_id.id),
    #             ('state', '=', 'open')
    #         ])
    
    def _check_participant_limit(self, agenda):
        """
        Verifica si hay cupos disponibles en la agenda
        """
        if agenda.quota_limited and agenda.quota_max:
            current_participants = self.search_count([
                ('agenda_id', '=', agenda.id),
                ('state', '=', 'open')
            ])
            if current_participants >= agenda.quota_max:
                return False
        return True
    
    @api.model
    def create(self, vals):
        if vals.get('state') == 'open':
            agenda = self.env['mz.agenda.elearning'].browse(vals.get('agenda_id'))
            if not self._check_participant_limit(agenda):
                raise UserError(f'No hay cupos disponibles en este curso. Por favor, registre al participante en estado "En espera".')
        return super().create(vals)
    
    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError('Solo se pueden confirmar registros en estado "En espera".')
        
        if not self._check_participant_limit(self.agenda_id):
            raise UserError(f'No hay cupos disponibles en este curso (# Máximo de inscripciones: {self.agenda_id.quota_max}). El participante debe permanecer en lista de espera.')
        
        return self.write({'state': 'open'})
    
    def action_cancel(self):
        self.ensure_one()
        if self.state != 'open':
            raise UserError('Solo se pueden cancelar registros en estado "Inscrito".')
        return self.write({'state': 'cancelled'})


class TrainingDay(models.Model):
    _name = 'training.day'
    _description = 'Día de Capacitación'
    _order = 'sequence'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(default=True)
    
   
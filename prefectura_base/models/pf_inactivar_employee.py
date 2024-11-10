from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from dateutil.relativedelta import relativedelta

class WizardInactivarEmployeeReasignarTurnos(models.TransientModel):
    _name = 'wizard.inactivar.employee.reasignar.turnos'
    _description = 'Wizard para Inactivar Empleado y Reasignar Turnos'

    empleado_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    fecha_Inactivacion = fields.Date(string='Fecha de Inactivación', required=True, default=fields.Date.today())
    nuevo_empleado_id = fields.Many2one('hr.employee', string='Nuevo Empleado')
    reasignar = fields.Boolean(string='Reasignar Turnos', default=True)
    mensaje_alerta = fields.Html(string='Mensaje de Alerta', compute='_compute_mensaje_alerta')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'empleado_id' in fields_list and self.env.context.get('active_id'):
            res['empleado_id'] = self.env.context['active_id']
        return res

    def action_reasignar_turnos(self):
        self.ensure_one()
        empleado = self.empleado_id
        planificaciones = self.env['mz.planificacion.servicio'].search([('generar_horario_id.personal_id', '=', empleado.id), ('estado', '=', 'activo'), ('fecha', '>=', fields.Date.today())])
        cabecera_planificacion = planificaciones.mapped('generar_horario_id')
        raise UserError('Por Definir ...')
        # if self.reasignar and self.nuevo_empleado_id:
            # for cabecera in cabecera_planificacion:
            #     # crear un nuevo registro de generar_horario
            #     nuevo_generar_horario = cabecera.copy()
            #     nuevo_generar_horario.personal_id = self.nuevo_empleado_id.id
            #     nuevo_generar_horario.fecha_inicio = self.fecha_Inactivacion
            #     nuevo_generar_horario.
            #     raise UserError(cabecera)

        empleado.write({'active': False}, {'fecha_inactivacion': self.fecha_Inactivacion})
        return {'type': 'ir.actions.act_window_close'}
    
    @api.depends('reasignar')
    def _compute_mensaje_alerta(self):
        for record in self:
            if record.reasignar:
                record.mensaje_alerta = '<div class="alert alert-warning">Este empleado tiene turnos activos en una planificación. Por favor, reasigne los turnos a otro empleado.</div>'
            else:
                record.mensaje_alerta = '<div class="alert alert-warning">Archivara todos los turnos del empleado.</div>'

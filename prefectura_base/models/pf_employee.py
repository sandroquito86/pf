from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta
from .. import utils

class PfEmployee(models.Model):
    _inherit = 'hr.employee'

    # Sobrescribir el campo para hacerlo accesible
    message_main_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Main Attachment',
        groups=False  # Quitar la restricción de grupos
    )
    if_autoridad = fields.Boolean(string='Es Autoridad', default=False)
    user_id = fields.Many2one('res.users', string='Usuario', ondelete='restrict')
    
    # Name fields
    nombre = fields.Char(string="Nombre", compute="_compute_name", store=True, readonly=True)
    apellido_paterno = fields.Char(string='Apellido Paterno')
    apellido_materno = fields.Char(string='Apellido Materno')
    primer_nombre = fields.Char(string='Primer Nombre')
    segundo_nombre = fields.Char(string='Segundo Nombre')
    tipo_documento = fields.Selection([
        ('dni', 'DNI'),
        ('pasaporte', 'Pasaporte'),
        ('carnet_extranjeria', 'Carnet de Extranjería')
    ], string='Tipo de Documento', required=True)
    
    # Other fields
    service_ids = fields.Many2many('gi.servicio', string="Servicios Asignados")
    edad = fields.Char(string="Edad", compute="_compute_edad", store=True)
    provincia_id = fields.Many2one("res.country.state", string="Provincia", domain="[('country_id', '=?', country_id)]")
    sucursal_id = fields.Many2one('pf.sucursal', string='Sucursal', required=True)
    programa_id = fields.Many2one('pf.programas', string='Programa', required=True)
    modulo_id = fields.Many2one('pf.modulo', string='Modulo', required=True)
    # revisar para que se creo este campo de modulo_ids un employee solo debe de pertenecer a un solo modulo 
    modulo_ids = fields.Many2many('pf.modulo', string="Módulos", help="Selecciona los módulos a los que pertenece este beneficiario")
    ciudad_id = fields.Many2one('res.country.ciudad', string='Ciudad' , ondelete='restrict', 
                                   domain="[('state_id', '=?', private_state_id)]")
    fecha_inactivacion = fields.Date(string='Fecha de Inactivación')
    tipo_personal = fields.Selection([('interno', 'Empleado Interno'), ('externo', 'Colaborador Externo')], string='Tipo de Personal', 
                                     default='interno', tracking=True, required=True, help="Indica si es un empleado de la institución o un colaborador externo")


    @api.onchange('tipo_documento', 'identification_id')
    def _onchange_documento(self):
        if self.tipo_documento == 'dni' and self.identification_id:
            if not utils.validar_cedula(self.identification_id):
                return {'warning': {
                    'title': "Cédula Inválida",
                    'message': "El número de cédula ingresado no es válido."
                }}
            
    @api.onchange('work_email')
    def _onchange_work_email(self):
        """
        Validate the email format.
        """
        if self.work_email and not utils.validar_email(self.work_email):
            return {
                'warning': {
                    'title': "Correo Electrónico Inválido",
                    'message': "El correo electrónico ingresado no es válido."
                }
            }
        
    def crear_user(self):
        user_vals = {
            'name': self.name,
            'login': self.work_email,
            'email': self.work_email,
            'company_id': self.company_id.id,
            'company_ids': [(4, self.company_id.id)],
            'password': self.identification_id,
            'programa_id': self.programa_id.id,
            # 'groups_id': [(6, 0, [self.env.ref('prefectura_base.group_portal').id])]
        }
        user = self.env['res.users'].create(user_vals)
        self.user_id = user.id
        return True

        
    @api.onchange('programa_id')
    def _onchange_programa_id(self):
        if self.programa_id:
            self.sucursal_id = self.programa_id.sucursal_id
            self.modulo_id = self.programa_id.modulo_id


    @api.constrains('user_id')
    def _check_unique_user(self):
        for employee in self:
            if employee.user_id:
                other_employee = self.search([
                    ('user_id', '=', employee.user_id.id),
                    ('id', '!=', employee.id)
                ])
                if other_employee:
                    raise ValidationError(_("El usuario %s ya está relacionado con un empleado.") % employee.user_id.name)

    @api.depends('birthday')
    def _compute_edad(self):
        for record in self:
            if record.birthday:
                hoy = date.today()
                diferencia = relativedelta(hoy, record.birthday)
                record.edad = f"{diferencia.years} años, {diferencia.months} meses, {diferencia.days} días"
            else:
                record.edad = "Sin fecha de nacimiento"

    @api.model
    def create(self, vals):        
        full_name = self._get_full_name(vals)
        vals['nombre'] = full_name     
        if 'name' not in vals:
            vals['name'] = full_name        
        employees = super(PfEmployee, self).create(vals)
        for employee in employees:
            employee.crear_user()
            if employee.user_id and employee.programa_id:
                employee.user_id.sudo().write({'programa_id': employee.programa_id.id})
        return employees

    def write(self, vals):
        name_fields = ['apellido_paterno', 'apellido_materno', 'primer_nombre', 'segundo_nombre']        
        if any(field in vals for field in name_fields):
            temp_vals = dict(self.read(['apellido_paterno', 'apellido_materno', 'primer_nombre', 'segundo_nombre'])[0])
            temp_vals.update({k: vals[k] for k in name_fields if k in vals})
            
            full_name = self._get_full_name(temp_vals)
            vals['nombre'] = full_name
            vals['name'] = full_name
        
        res = super(PfEmployee, self).write(vals)
        if 'user_id' in vals or 'programa_id' in vals:
            for employee in self:
                if employee.user_id and employee.programa_id:
                    employee.user_id.sudo().write({'programa_id': employee.programa_id.id})
        return res

    def _get_full_name(self, record):
        if isinstance(record, dict):
            nombres = filter(None, [
                record.get('apellido_paterno', ''),
                record.get('apellido_materno', ''),
                record.get('primer_nombre', ''),
                record.get('segundo_nombre', '')
            ])
        else:
            nombres = filter(None, [
                record.apellido_paterno,
                record.apellido_materno,
                record.primer_nombre,
                record.segundo_nombre
            ])
        return " ".join(nombres) or "Sin nombre"

    @api.depends('apellido_paterno', 'apellido_materno', 'primer_nombre', 'segundo_nombre')
    def _compute_name(self):
        for record in self:
            full_name = self._get_full_name(record)
            record.nombre = full_name
            record.name = full_name
            if record.resource_id:
                record.resource_id.name = full_name

    @api.constrains('nombre', 'apellido_paterno', 'apellido_materno', 'primer_nombre', 'segundo_nombre')
    def _check_name_not_empty(self):
        for record in self:
            if not record.nombre:
                raise ValidationError("El nombre no puede estar vacío. Por favor, proporcione al menos un nombre o apellido.")
            

    def action_inactivar_empleado(self):
        self.ensure_one()
        planificaciones = self.env['mz.planificacion.servicio'].search([('generar_horario_id.personal_id', '=', self.id), ('estado', '=', 'activo'), ('fecha', '>=', date.today())])
        if planificaciones:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Reasignar Turnos',
                'res_model': 'wizard.inactivar.employee.reasignar.turnos',
                'view_mode': 'form',
                'view_id': self.env.ref('prefectura_base.view_wizard_reasignar_turnos_form').id,
                'target': 'new',
                'context': {
                    'default_empleado_id': self.id,
                },
            }
        else:
            self.active = False
            self.fecha_inactivacion = date.today()
            return {'type': 'ir.actions.act_window_close'}
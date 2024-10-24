from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

class ServiceStaff(models.Model):
    _name = 'gi.personal'
    _description = 'Personal encargado de brindar servicios'
    _inherits = {'hr.employee': 'employee_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, ondelete="cascade")
    nombre = fields.Char(string="Nombre", compute="_compute_name", store=True, readonly=True)
    apellido_paterno = fields.Char(string='Apellido Paterno')
    apellido_materno = fields.Char(string='Apellido Materno')
    primer_nombre = fields.Char(string='Primer Nombre')
    segundo_nombre = fields.Char(string='Segundo Nombre')  
    service_ids = fields.Many2many('gi.servicio', string="Servicios Asignados")
    edad = fields.Char(string="Edad", compute="_compute_edad", store=True)
    provincia_id = fields.Many2one("res.country.state", string="Provincia", domain="[('country_id', '=?', country_id)]")

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
        if 'employee_id' not in vals:
            nombre_completo = self._get_full_name(vals)
            if not nombre_completo:
                raise ValidationError("El nombre no puede estar vacío. Por favor, proporcione al menos un nombre o apellido.")
            
            employee_vals = {
                'name': nombre_completo,
                # Otros campos necesarios para hr.employee...
            }
            employee = self.env['hr.employee'].create(employee_vals)
            vals['employee_id'] = employee.id

            resource_vals = {
                'name': nombre_completo,
                'resource_type': 'user',
            }
            if employee.resource_id:
                employee.resource_id.write(resource_vals)
            else:
                resource = self.env['resource.resource'].create(resource_vals)
                employee.resource_id = resource.id

        # Asegurarse de que el campo 'nombre' tenga un valor
        if 'nombre' not in vals or not vals['nombre']:
            vals['nombre'] = self._get_full_name(vals)

        return super(ServiceStaff, self).create(vals)

    def write(self, vals):
        # Actualizar el nombre si alguno de los campos relacionados cambia
        if any(field in vals for field in ['apellido_paterno', 'apellido_materno', 'primer_nombre', 'segundo_nombre']):
            vals['nombre'] = self._get_full_name({**self.read()[0], **vals})
        
        result = super(ServiceStaff, self).write(vals)
        
        # Actualizar el nombre en el empleado y el recurso asociado
        if 'nombre' in vals:
            self.employee_id.write({'name': vals['nombre']})
            if self.employee_id.resource_id:
                self.employee_id.resource_id.write({'name': vals['nombre']})
        
        return result

    def _get_full_name(self, record):
        """
        Construye el nombre completo basado en los campos individuales.
        Retorna una cadena vacía si no hay datos.
        """
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
            record.nombre = self._get_full_name(record)
            if record.employee_id:
                record.employee_id.name = record.nombre
                if record.employee_id.resource_id:
                    record.employee_id.resource_id.name = record.nombre

    @api.constrains('nombre', 'apellido_paterno', 'apellido_materno', 'primer_nombre', 'segundo_nombre')
    def _check_name_not_empty(self):
        for record in self:
            if not record.nombre:
                raise ValidationError("El nombre no puede estar vacío. Por favor, proporcione al menos un nombre o apellido.")
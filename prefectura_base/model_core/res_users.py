from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    programa_id = fields.Many2one(
        string='Programa',
        comodel_name='pf.programas', 
        ondelete='restrict',
    )

    @api.constrains('employee_ids')
    def _check_unique_employee(self):
        for user in self:
            if len(user.employee_ids) > 1:
                raise ValidationError(_("Un usuario no puede estar vinculado a múltiples empleados."))

    @api.model
    def create(self, vals):
        user = super(ResUsers, self).create(vals)
        if not user.programa_id:
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            if employee and employee.programa_id:
                user.programa_id = employee.programa_id
        return user

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['programa_id']

    def write(self, values):
        result = super(ResUsers, self).write(values)
        if 'programa_id' in values:
            # Forzar una actualización de la sesión
            self.env['ir.http']._auth_method_user()
        return result
from odoo import models, fields, api

class ConfirmUnpublishWizard(models.TransientModel):
    _name = 'confirm.unpublish.wizard'
    _description = 'Confirm Unpublish Wizard'

    message = fields.Text(string="Mensaje", default="¿Está seguro de que desea retirar la publicación?")
    aux = fields.Integer(string="Auxiliar")

    def action_confirm(self):
        # Lógica para ejecutar la acción de despublicar
        active_id = self.env.context.get('active_id')
        if active_id:
            if self.aux == 1:
                programa = self.env['pf.programas'].browse(active_id)
                programa.action_unpublish()
            elif self.aux == 2:
                servicio = self.env['mz.asignacion.servicio'].browse(active_id)
                servicio.action_unpublish()
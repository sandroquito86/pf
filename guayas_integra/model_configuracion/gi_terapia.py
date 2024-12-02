from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from dateutil.relativedelta import relativedelta

class Terapia(models.Model):
    _name = 'gi.terapias'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Terapias'

    @api.model
    def _get_tipo_servicio_domain(self):
        catalogo_id = self.env.ref('prefectura_base.catalogo_terapias').id
        return [('catalogo_id', '=', catalogo_id)]

    name = fields.Char(string='Nombre', required=True, tracking=True)
    descripcion = fields.Text(string='Descripción', tracking=True)
    if_derivacion = fields.Boolean(default=False, string='Derivación', tracking=True)
    image = fields.Binary(string='Imagen', attachment=True)
    catalogo_tipo_terapia_id = fields.Many2one('pf.items', string='Tipo de Terapia',  domain=_get_tipo_servicio_domain, tracking=True)
    active = fields.Boolean(default=True, string='Activo', tracking=True)
    has_been_used = fields.Boolean(
        string='Ha sido utilizado',
        compute='_compute_has_been_used'
    )

    @api.depends()
    def _compute_has_been_used(self):
        for record in self:
            # Buscar si el sub-servicio ha sido usado en agendamientos
            used_in_agendar = self.env['gi.asignacion.terapia'].search_count([
                ('terapia_id', '=', record.id)
            ]) > 0
            
            # Puedes agregar más condiciones según tus necesidades
            record.has_been_used = used_in_agendar

    def unlink(self):
        if any(record.has_been_used for record in self):
            raise UserError('No se pueden eliminar Terapia que ya han sido utilizados. En su lugar, desactívelos(Archivar).')
        return super().unlink() 
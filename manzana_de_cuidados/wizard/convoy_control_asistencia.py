from odoo import models, fields,api

class MZConvoyControlAsistencia(models.TransientModel):
    _name = 'mz.control_asistencia'
    _description = 'Control de Asistencia Wizard'


    @api.model
    def default_servicio_id(self): 
        active_id = self._context.get('active_id') 
        asistencia = self.env['mz.asistencia_servicio']
        if active_id:
            asistencia = asistencia.browse(self._context.get('active_id'))         
        return asistencia.servicio_base_id.id

    observacion = fields.Text(string='Observación', required=True)
    servicio_id = fields.Many2one(comodel_name='mz.servicio', string='Servicio',default=default_servicio_id)
    sub_servicio_id = fields.Many2one(comodel_name='mz.sub.servicio', string='Sub Servicio',domain="[('servicio_id', '=', servicio_id)]")
    tiene_subservicios = fields.Boolean(string='¿Tiene Subservicios?', compute='_compute_tiene_subservicios')


    @api.depends('servicio_id')
    def _compute_tiene_subservicios(self):
        for record in self:
            if record.servicio_id:
                record.tiene_subservicios = bool(record.servicio_id.sub_servicio_ids)
            else:
                record.tiene_subservicios = False


    def action_confirm(self):
        active_id = self._context.get('active_id') 
        asistencia = self.env['mz.asistencia_servicio']
        if active_id:
            asistencia = asistencia.browse(self._context.get('active_id'))
            asistencia.write({'observacion': self.observacion,
                              'sub_servicio_id': self.sub_servicio_id.id,                                                          
                                })
            asistencia.action_asistio()
        # Lógica personalizada para manejar la confirmación
        return {'type': 'ir.actions.act_window_close'}


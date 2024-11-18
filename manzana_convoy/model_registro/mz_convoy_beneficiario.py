from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ConvoyBeneficiarioRel(models.Model):
    _name = 'mz_convoy.beneficiario'
    _description = 'Relación Convoy Beneficiario'
    _rec_name = 'beneficiario_id'
    _order = 'fecha_registro desc'

    # Campos de Relación
    convoy_id = fields.Many2one('mz.convoy', string='Convoy', required=True, ondelete='restrict')
    beneficiario_id = fields.Many2one('mz.beneficiario', string='Beneficiario', required=True, ondelete='restrict')
    # Campos de Control
    tipo_registro = fields.Selection([('masivo', 'Registro Masivo'), ('asistencia', 'Registro por Asistencia'), ('socioeconomico', 'Registro Socioeconómico')],
                                     string='Tipo de Registro', required=True)
    fecha_registro = fields.Datetime(string='Fecha de Registro', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Registrado por', default=lambda self: self.env.user,  required=True, readonly=True)
    # Campos de Servicio
    servicio_id = fields.Many2one('mz.servicio', string='Servicio', domain="[('convoy_id', '=', convoy_id)]")
    estado = fields.Selection([('pendiente', 'Pendiente'), ('atendido', 'Atendido')], string='Estado', default='pendiente', required=True)
    # Campos relacionados para información rápida
    numero_documento = fields.Char(related='beneficiario_id.numero_documento', string='Número de Documento', store=True)
    nombres_completos = fields.Char(compute='_compute_nombres_completos', store=True, string='Nombres Completos')

    _sql_constraints = [('unique_beneficiario_convoy', 'UNIQUE(beneficiario_id, convoy_id)', 'El beneficiario ya está registrado en este convoy!')]

    def action_promover_asistencia(self):
        self.ensure_one()
        if self.tipo_registro != 'masivo':
            raise UserError(_('Solo los registros masivos pueden ser promovidos a asistencia.'))
        
        return {
            'name': _('Promover a Asistencia'),
            'type': 'ir.actions.act_window',
            'res_model': 'mz_convoy.beneficiario_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tipo_registro': 'asistencia',
                'default_convoy_id': self.convoy_id.id,
                'default_numero_documento': self.numero_documento,
                'promover_registro': True
            }
        }

    def action_promover_socioeconomico(self):
        self.ensure_one()
        if self.tipo_registro not in ['masivo', 'asistencia']:
            raise UserError(_('Solo los registros masivos o de asistencia pueden ser promovidos a socioeconómico.'))
        
        return {
            'name': _('Promover a Socioeconómico'),
            'type': 'ir.actions.act_window',
            'res_model': 'mz_convoy.beneficiario_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tipo_registro': 'socioeconomico',
                'default_convoy_id': self.convoy_id.id,
                'default_numero_documento': self.numero_documento,
                'promover_registro': True
            }
        }

    @api.depends('beneficiario_id')
    def _compute_nombres_completos(self):
        for record in self:
            if record.beneficiario_id:
                nombres = [
                    record.beneficiario_id.apellido_paterno,
                    record.beneficiario_id.apellido_materno,
                    record.beneficiario_id.primer_nombre,
                    record.beneficiario_id.segundo_nombre
                ]
                record.nombres_completos = ' '.join(filter(None, nombres))
            else:
                record.nombres_completos = False

    # @api.constrains('servicio_id', 'tipo_registro')
    # def _check_servicio_required(self):
    #     for record in self:
    #         if record.tipo_registro in ['asistencia', 'socioeconomico'] and not record.servicio_id:
    #             raise UserError(_('El servicio es requerido para registros de tipo Asistencia y Socioeconómico.'))

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.beneficiario_id.numero_documento} - {record.nombres_completos}"
            result.append((record.id, name))
        return result
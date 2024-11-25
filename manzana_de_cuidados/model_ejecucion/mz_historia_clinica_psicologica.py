from odoo import models, fields, api

class HistoriaPsicologica(models.Model):
    _name = 'mz.historia.psicologica'
    _description = 'Historia Psicológica'
    _order = 'fecha desc'
    _rec_name = 'consulta_id'

    beneficiario_id = fields.Many2one('mz.beneficiario', string='Paciente Beneficiario', ondelete='cascade')
    personal_id = fields.Many2one('hr.employee', string='Personal Psicológico', ondelete='restrict')
    consulta_id = fields.Many2one('mz.consulta.psicologica', string='Consulta Relacionada', ondelete='cascade')
    fecha = fields.Date(string='Fecha')
    
    # Campos específicos para historia psicológica
    motivo_consulta = fields.Text(string='Motivo de Consulta')
    estado_emocional = fields.Text(string='Estado Emocional')
    antecedentes_relevantes = fields.Text(string='Antecedentes Relevantes')
    evaluacion_inicial = fields.Text(string='Evaluación Inicial')
    plan_intervencion = fields.Text(string='Plan de Intervención')
    observaciones = fields.Text(string='Observaciones')
    
    diagnostico_ids = fields.One2many(
        'mz.diagnostico.psicologico.linea',
        'historia_psicologica_id',
        string='Diagnósticos'
    )

    dependiente_id = fields.Many2one('mz.dependiente', string='Paciente Dependiente', ondelete='cascade')
    
    tipo_paciente = fields.Selection([
        ('titular', 'Titular'),
        ('dependiente', 'Dependiente')
    ], string='Tipo de Paciente')

    def name_get(self):
        result = []
        for record in self:
            if record.beneficiario_id:
                name = f"Historia Clínica - {record.beneficiario_id.name} - {record.fecha}"
            else:
                name = f"Historia Clínica - {record.dependiente_id.name} - {record.fecha}"
            result.append((record.id, name))
        return result
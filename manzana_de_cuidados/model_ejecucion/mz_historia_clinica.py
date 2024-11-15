from odoo import models, fields, api

class HistoriaClinica(models.Model):
    _name = 'mz.historia.clinica'
    _description = 'Historia Clínica'
    _order = 'fecha desc'
    _rec_name = 'beneficiario_id'

    beneficiario_id = fields.Many2one('mz.beneficiario', string='Paciente', ondelete='cascade')

    personal_id = fields.Many2one('hr.employee', string='Personal Medico', ondelete='restrict')
    sintomas = fields.Text(string='Síntomas')
    consulta_id = fields.Many2one('mz.consulta', string='Consulta Relacionada', ondelete='cascade')
    fecha = fields.Date(string='Fecha')
    motivo_consulta = fields.Text(string='Motivo de Consulta')
    tratamiento = fields.Text(string='Tratamiento')
    observaciones = fields.Text(string='Observaciones')
    signos_vitales = fields.Text(string='Signos Vitales')
    # Historial de antecedentes médico
    antecedentes_personales = fields.Text(string='Antecedentes Personales', tracking=True)
    antecedentes_familiares = fields.Text(string='Antecedentes Familiares', tracking=True)
    alergias = fields.Text(string='Alergias', tracking=True)
    medicamentos_actuales = fields.Text(string='Medicamentos Actuales', tracking=True)
    diagnostico_ids = fields.One2many(
        'mz.diagnostico.linea',
        'historia_clinica_id',
        string='Diagnósticos'
    )
    dependiente_id = fields.Many2one('mz.dependiente', string='Dependiente', ondelete='cascade')

    def name_get(self):
        return [(record.id, f"Historia Clínica - {record.beneficiario_id.name} - {record.fecha}") for record in self]
    
    
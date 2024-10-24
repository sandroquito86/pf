from odoo import models, fields, api

class HistoriaClinica(models.Model):
    _name = 'mz.historia.clinica'
    _description = 'Historia Clínica'
    _order = 'fecha desc'

    beneficiario_id = fields.Many2one('mz.beneficiario', string='Paciente', required=True, ondelete='cascade')
    consulta_id = fields.Many2one('mz.consulta', string='Consulta Relacionada', required=True, ondelete='cascade')
    fecha = fields.Date(string='Fecha', required=True)
    motivo_consulta = fields.Text(string='Motivo de Consulta')
    diagnostico = fields.Text(string='Diagnóstico')
    tratamiento = fields.Text(string='Tratamiento')
    observaciones = fields.Text(string='Observaciones')
    signos_vitales = fields.Text(string='Signos Vitales')
    cie10_id = fields.Many2one('pf.cie10', string='Diagnóstico CIE-10', tracking=True)
    # Historial de antecedentes médico
    antecedentes_personales = fields.Text(string='Antecedentes Personales', tracking=True)
    antecedentes_familiares = fields.Text(string='Antecedentes Familiares', tracking=True)
    alergias = fields.Text(string='Alergias', tracking=True)
    medicamentos_actuales = fields.Text(string='Medicamentos Actuales', tracking=True)

    def name_get(self):
        return [(record.id, f"Historia Clínica - {record.beneficiario_id.name} - {record.fecha}") for record in self]
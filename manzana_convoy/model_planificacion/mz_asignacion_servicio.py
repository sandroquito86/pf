# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from string import ascii_letters, digits
import string


class AsignarServicio(models.Model):
    _inherit = 'mz.asignacion.servicio'   

    convoy_id = fields.Many2one('mz.convoy', string='Convoy', required=True, tracking=True)
    domain_convoy_id = fields.Char(string='Domain Convoy',compute='_compute_domain_convoy')    
    numero_turnos = fields.Integer(string='Cantidad de turnos',)

    
    def eliminar_desde_o2m(self):
        self.ensure_one()
        if self.convoy_id:
            planificaciones = self.env['mz.genera.planificacion.servicio'].search([
                ('servicio_id', '=', self.id)
            ])
            
            # Verificar turnos asignados
            for plan in planificaciones:
                if plan.turno_disponibles_ids:
                    raise UserError(
                        f"No se puede eliminar porque la planificación '{plan.name}' "
                        "ya tiene turnos asignados."
                    )
            
            # Eliminar planificaciones relacionadas
            planificaciones.unlink()
            
            # Eliminar registros de personal con contexto especial
            with self.env.cr.savepoint():
                # Usando context para evitar el constraint
                self.with_context(eliminar_registro=True).write({
                    'personal_ids': [(5, 0, 0)]
                })
                
                # Eliminar el registro principal
                self.env.cr.execute("""
                    DELETE FROM mz_asignacion_servicio WHERE id = %s
                """, (self.id,))
                
        return True

    # Para eliminación desde la vista principal (se mantiene igual)
    def unlink(self):
        for record in self:
            if record.convoy_id:  # Solo para registros de convoy
                # Buscar registros de planificación asociados
                planificaciones = self.env['mz.genera.planificacion.servicio'].search([
                    ('servicio_id', '=', record.id)
                ])
                
                # Verificar cada planificación
                for plan in planificaciones:
                    if plan.turno_disponibles_ids:
                        raise UserError(f"No se puede eliminar porque la planificación '{plan.name}' ya tiene turnos asignados.")
                    else:
                        plan.unlink()
                        
                return super(AsignarServicio, self).unlink()
            else:
                raise UserError("Solo se pueden eliminar registros de convoy.")

    def action_archivar_servicio(self):
        for record in self:
            if not record.convoy_id:
                raise UserError("Solo se pueden archivar registros de convoy.")
            
            # Verificamos si hay planificaciones con turnos
            planificaciones = self.env['mz.genera.planificacion.servicio'].search([
                ('servicio_id', '=', record.id)
            ])
            
            for plan in planificaciones:
                if plan.turno_disponibles_ids:
                    raise UserError(f"No se puede archivar porque la planificación '{plan.name}' ya tiene turnos asignados.")
                else:
                    plan.active = False
            
            # Archivamos el registro de servicio
            record.active = False

    def write(self, vals):
        if 'personal_ids' in vals and self.convoy_id:  # Solo para registros de convoy
            command = vals['personal_ids'][0]  # El comando many2many
            
            # Obtenemos los IDs actuales
            current_ids = set(self.personal_ids.ids)
            
            if command[0] == 6:  # SET - Reemplazar todos
                new_ids = set(command[2])
                # IDs a eliminar
                to_remove = current_ids - new_ids
                # IDs a agregar
                to_add = new_ids - current_ids
                
            elif command[0] == 3:  # REMOVE
                to_remove = {command[1]}
                to_add = set()
                
            elif command[0] == 4:  # ADD
                to_remove = set()
                to_add = {command[1]}
                
            elif command[0] == 5:  # CLEAR
                to_remove = current_ids
                to_add = set()
            
            # Manejo de eliminaciones
            for empleado_id in to_remove:
                planificacion = self.env['mz.genera.planificacion.servicio'].search([
                    ('servicio_id', '=', self.id),
                    ('personal_id', '=', empleado_id)
                ])
                
                if planificacion:
                    if planificacion.turno_disponibles_ids:
                        raise UserError(f"No se puede eliminar el empleado porque ya tiene turnos asignados en la planificación.")
                    else:
                        planificacion.unlink()
            
            # Manejo de adiciones
            for empleado_id in to_add:
                self.env['mz.genera.planificacion.servicio'].create({
                    'servicio_id': self.id,
                    'programa_id': self.programa_id.id,
                    'name': f'Horario - {self.name}',
                    'estado': 'borrador',
                    'personal_id': empleado_id,
                })
        return super(AsignarServicio, self).write(vals)
    
    @api.depends('servicio_id')
    def _compute_domain_convoy(self):
        for record in self:
            # Buscar los convoy en estado aprobado
            convoys_aprobados = self.env['mz.convoy'].search([
                ('state', '=', 'aprobado')
            ])
            if convoys_aprobados:
                record.domain_convoy_id = [('id', 'in', convoys_aprobados.ids)]
            else:
                record.domain_convoy_id = [('id', 'in', [])]

    @api.onchange('convoy_id')
    def _onchange_convoy_id(self):        
        if self.convoy_id:
            self.programa_id = self.convoy_id.programa_id   


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Obtenemos el convoy relacionado con el programa
            convoy = self.env['mz.convoy'].search([('programa_id', '=', vals.get('programa_id'))], limit=1)
            if convoy:
                vals['convoy_id'] = convoy.id
        
        asignaciones = super(AsignarServicio, self).create(vals_list)
        
        for asignacion in asignaciones:
            if asignacion.convoy_id and asignacion.personal_ids:
                for empleado in asignacion.personal_ids:
                    self.env['mz.genera.planificacion.servicio'].create({
                        'servicio_id': asignacion.id,
                        'programa_id': asignacion.programa_id.id,
                        'name': f'Horario - {asignacion.name}',
                        'estado': 'confirmado',
                        'personal_id': empleado.id,
                    })
        
        return asignaciones
   
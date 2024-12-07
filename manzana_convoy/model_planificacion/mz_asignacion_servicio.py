# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from string import ascii_letters, digits
import string


class AsignarServicio(models.Model):
    _inherit = 'mz.asignacion.servicio'   

    convoy_id = fields.Many2one('mz.convoy', string='Convoy', required=False, tracking=True)
    state = fields.Selection(related='convoy_id.state', readonly=True, store=True,tracking=True)  

    domain_convoy_id = fields.Char(string='Domain Convoy',compute='_compute_domain_convoy')    
    numero_turnos = fields.Integer(string='Cantidad de turnos',)


    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar servicios cuando viene el contexto
        """
        args = args or []
        user = self.env.user
        base_args = [('id', '=', -1)]  # Dominio imposible por defecto
        if self._context.get('filtrar_convoy'):
            # Verificar grupos
            if user.has_group('manzana_convoy.group_mz_convoy_coordinador'):
                # Para coordinador: ver solo servicios de su convoy
                convoy_ids = self.env['mz.convoy'].search([
                    ('director_coordinador.user_id', '=', user.id)
                ]).ids
                base_args = [('convoy_id', 'in', convoy_ids)]
            elif user.has_group('manzana_convoy.group_mz_convoy_administrador'):
                # Para admin/asistente: ver servicios con modulo_id = 4
                base_args = [('programa_id.modulo_id', '=', 4)]
            elif user.has_group('manzana_convoy.group_mz_convoy_operador'):
                # Para operador: ver solo servicios de convoyes donde está asignado y están en ejecución
                convoy_ids = self.env['mz.convoy'].search([
                    ('state', '=', 'ejecutando'),
                    ('operadores_ids', 'in', user.employee_id.id)
                ]).ids
                base_args = [('convoy_id', 'in', convoy_ids)]
            args = base_args + args
        return super(AsignarServicio, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
    
    def eliminar_desde_o2m(self):
        self.ensure_one()
        if self.convoy_id:
            # Validar estado del convoy
            if self.convoy_id.state != 'aprobado':  # Asumiendo que 'aprobado' es el estado de aprobado
                raise UserError("Solo se pueden eliminar registros cuando el convoy está en estado aprobado.")
                
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

    def unlink(self):
        for record in self:
            if record.convoy_id:  # Solo para registros de convoy
                # Validar estado del convoy
                if record.convoy_id.state != 'aprobado':
                    raise UserError("Solo se pueden eliminar registros cuando el convoy está en estado aprobado.")
                    
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
                
            # Validar estado del convoy
            if record.convoy_id.state != 'aprobado':
                raise UserError("Solo se pueden archivar registros cuando el convoy está en estado aprobado.")
                
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
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Obtenemos el convoy relacionado con el programa
            convoy = self.env['mz.convoy'].search([('programa_id', '=', vals.get('programa_id'))], limit=1)
            if convoy:
                vals['convoy_id'] = convoy.id
        
        asignaciones = super(AsignarServicio, self).create(vals_list)
        
        # Solo crear planificaciones para registros con convoy_id
        for asignacion in asignaciones:
            if asignacion.convoy_id and asignacion.personal_ids:
                for empleado in asignacion.personal_ids:
                    self.env['mz.genera.planificacion.servicio'].create({
                        'servicio_id': asignacion.id,
                        'programa_id': asignacion.programa_id.id,
                        'personal_id': empleado.id,
                        'convoy_id': asignacion.convoy_id.id,  # Añadimos el convoy_id
                        'name': f'Horario - {asignacion.name}',
                        'estado': 'borrador',
                        'fecha_inicio': asignacion.convoy_id.fecha_inicio_evento,  # Añadimos fecha inicio del convoy
                        'fecha_fin': asignacion.convoy_id.fecha_hasta_evento,  # Añadimos fecha fin del convoy
                        'maximo_beneficiarios': 1,
                    })
                    
        
        return asignaciones

    def write(self, vals):
        if 'personal_ids' in vals and self.convoy_id:
            command = vals['personal_ids'][0]
            current_ids = set(self.personal_ids.ids)
            
            if command[0] == 6:  # SET
                new_ids = set(command[2])
                to_remove = current_ids - new_ids
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
                    ('personal_id', '=', empleado_id),
                    ('convoy_id', '=', self.convoy_id.id)  # Añadimos filtro por convoy
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
                    'personal_id': empleado_id,
                    'convoy_id': self.convoy_id.id,  # Añadimos el convoy_id
                    'name': f'Horario - {self.name}',
                    'estado': 'borrador',
                    'fecha_inicio': self.convoy_id.fecha_inicio,  # Añadimos fecha inicio del convoy
                    'fecha_fin': self.convoy_id.fecha_fin,  # Añadimos fecha fin del convoy
                    'maximo_beneficiarios': 1,
                })

        # Si se está actualizando el convoy_id
        if 'convoy_id' in vals:
            new_convoy = self.env['mz.convoy'].browse(vals['convoy_id'])
            # Actualizar las planificaciones existentes
            planificaciones = self.env['mz.genera.planificacion.servicio'].search([
                ('servicio_id', '=', self.id)
            ])
            for plan in planificaciones:
                if not plan.turno_disponibles_ids:
                    plan.write({
                        'convoy_id': new_convoy.id,
                        'programa_id': new_convoy.programa_id.id,
                        'fecha_inicio': new_convoy.fecha_inicio,
                        'fecha_fin': new_convoy.fecha_fin,
                    })
                else:
                    raise UserError("No se puede cambiar el convoy porque ya existen turnos asignados.")
            
            # Actualizar el programa_id si cambia el convoy
            vals['programa_id'] = new_convoy.programa_id.id
            
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


    
   
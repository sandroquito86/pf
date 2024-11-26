/** @odoo-module */

import { registry } from "@web/core/registry";

import { useService } from "@web/core/utils/hooks";

import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { CheckBox } from "@web/core/checkbox/checkbox";
const { DateTime } = luxon;

import { Component, useState, onMounted, useEffect, EventBus } from "@odoo/owl";



export class AttendanceBeneficiary extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.bus = new EventBus();

        this.state = useState({
            agenda : this.env.model.root.evalContext.agenda_id,
            beneficiaries : [],
            isAttendanceSubmitted: false,
            attend: false,
            dateUi: DateTime.local().toFormat('dd/MM/yyyy'),
            date: luxon.DateTime.fromISO(this.env.model.root.evalContext.start_date),
            today: luxon.DateTime.now(),
            allowedDates: new Set()
        });

        
        onMounted(async ()=>{
            console.log(this.bus)
            await this.loadPlannedDates();
            await this.checkAndLoadAttendance();
        })

        useEffect(
            () => {
                // Función asíncrona autoejecutable
                (async () => {
                    if (this.state.date) {
                        await this.checkAndLoadAttendance();
                    }
                })();

                // Retornar función de limpieza
                return () => {
                    // Limpiar recursos si es necesario
                    this.state.beneficiaries = [];
                    this.state.isAttendanceSubmitted = false;
                };
            },
            () => [this.state.date]
        );
    }

    async loadPlannedDates() {
        try {
            const sessions = await this.orm.searchRead(
                'mz.planificacion.sesiones',
                [['horario_id', '=', this.state.agenda]],
                ['date'],
                { order: 'date asc' }
            );
            this.state.allowedDates = new Set(
                sessions.map(session => session.date)
            );
        } catch (error) {
            console.error("Error cargando fechas planificadas:", error);
        }
    }

    async checkAndLoadAttendance() {
        console.log(this.env.model.root.evalContext)
        const hasAttendance = await this.checkIfAttendance();
            if (hasAttendance) {
                this.state.isAttendanceSubmitted = true;
                return;
            }

            const { agenda } = this.state;
            let attendees = await this._showAttendees(agenda);
            this.state.beneficiaries = attendees?.course_attendees;
    }

    isDateValid(date) {
        if (!date) return false;
        const formattedDate = date.toFormat('yyyy-MM-dd');
        const isValid = this.state.allowedDates.has(formattedDate);
        return isValid;
    }

    async _showAttendees(agenda) {
        try {
            const configs = await this.rpc("/manzana_beneficiary/attendees", {
                agenda: agenda
            });
            const beneficiaries = JSON.parse(configs)
            return beneficiaries
        } catch (error) {
            console.error("Error en la llamada RPC:", error);
        }
    }

    // onDateInput(ev) {
    //     if (this.isDateValid(ev.toJSDate())) {
    //         this.state.date = ev;
    //     }
    // }

    onDateChanged(ev) {
        this.state.date = ev;
    }

    onOptionChanged(beneficiaryId, state) {
        const beneficiary = this.state.beneficiaries.find(b => b.id === beneficiaryId);
        if (beneficiary && state === 'absent' ) {
            beneficiary[state] = !beneficiary[state]
            beneficiary.attendance = !beneficiary[state]
            beneficiary.justified = false
            
        } else if (beneficiary && state === 'justified') {
            beneficiary[state] = !beneficiary[state]
        }else {
            console.warn(`No se encontró asistencia para el beneficiario ${beneficiaryId}`);
        }
    }

    displayNotification(text, alert){
        this.notification.add(text, { type: alert });
    }

    async checkIfAttendance() {
        try {
            const date = this.state.date.toFormat('dd/MM/yyyy')
            const formattedDate = this.formattedDate(date)
            const attendance = await this.orm.searchCount('mz.attendance.student', [
                ['agenda_id', '=', this.state.agenda],
                ['date', '=', formattedDate]
            ]);
            return attendance > 0;
        } catch (error) {
            console.error("Error checking attendance:", error);
            return false;
        }
    }

    async saveAttendances() {
        const beneficiariesStudents = this.state.beneficiaries.filter(b => b.student_id)
        const date = this.state.date.toFormat('dd/MM/yyyy')
        const values = beneficiariesStudents.map(b => this.prepareValuesForCreate(b, this.state.agenda, date))
        try {
            await this.orm.create('mz.attendance.student', values);
            this.state.isAttendanceSubmitted = true
            const msg = `La asistencia del día ${date} ha sido registrada correctamente.`
            this.displayNotification(msg, "success")
        } catch (error) {
            const msg = `Ha existido un error al intentar guardar la asistencia del día de hoy.`
            this.displayNotification(msg, "danger")
            console.error("Error al guardar las asistencias:", error);
        }
    }

    prepareValuesForCreate(beneficiary, agenda, date) {
        let attendance = beneficiary.attendance ? 'present' : 'absent';
        let subState = attendance === 'absent' ? (beneficiary.justified ? 'jst' : 'wjst') : 'na';
        const formattedDate = this.formattedDate(date)
        return {
            'student_id': beneficiary.student_id,
            'agenda_id': agenda,
            'date': formattedDate,
            'state': attendance,
            'sub_state': subState
        };
    }

    formattedDate(date) {
        let dateObj;
        if (typeof date === 'string') {
            dateObj = DateTime.fromFormat(date, 'dd/MM/yyyy').toJSDate();
        } else if (date instanceof DateTime) {
            dateObj = date.toJSDate();
        } else {
            dateObj = new Date(date);
        }
        if (isNaN(dateObj.getTime())) {
            console.error('Fecha inválida:', date);
            throw new Error('Fecha inválida');
        }
    
        return dateObj.toISOString().split('T')[0];
    }
}

AttendanceBeneficiary.template = "manzana_elearning.attendance_beneficiary";
AttendanceBeneficiary.components = { DatePicker: DateTimePicker, DateTimeInput, CheckBox };

export const attendanceBeneficiary = {
    component: AttendanceBeneficiary
};
registry.category("view_widgets").add("mze_attendance_beneficiary", attendanceBeneficiary);
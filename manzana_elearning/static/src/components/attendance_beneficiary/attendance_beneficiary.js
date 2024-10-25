/** @odoo-module */

import { registry } from "@web/core/registry";

import { useService } from "@web/core/utils/hooks";

import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { CheckBox } from "@web/core/checkbox/checkbox";
const { DateTime } = luxon;

import { Component, useState, onMounted } from "@odoo/owl";



export class AttendanceBeneficiary extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            slideChanel : this.env.model.root.evalContext.id,
            beneficiaries : [],
            isAttendanceSubmitted: false,
            attend: false,
            dateToday: DateTime.local().toFormat('dd/MM/yyyy'),
            date: luxon.DateTime.now(),
            today: luxon.DateTime.now(),
        });

        onMounted(async ()=>{
            const hasAttendance = await this.checkTodayAttendance();
            if (hasAttendance) {
                this.state.isAttendanceSubmitted = true;
                return;
            }

            const { slideChanel } = this.state;
            let attendees = await this._showAttendees(slideChanel);
            this.state.beneficiaries = attendees?.course_attendees;
        })
    }

    async _showAttendees(slideChanel) {
        
        try {
            const configs = await this.rpc("/manzana_beneficiary/attendees", {
                slideChanel: slideChanel
            });
            const beneficiaries = JSON.parse(configs)
            return beneficiaries
        } catch (error) {
            console.error("Error en la llamada RPC:", error);
        }
    }

    onDateChanged(ev) {
        const date = ev.toFormat('dd/MM/yyyy');
    }

    onOptionChanged(beneficiaryId, state) {
        const beneficiary = this.state.beneficiaries.find(b => b.id === beneficiaryId); //evaluar el objeto
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

    displayNotification(text){
        this.notification.add(text, { type: "success" });
    }

    async checkTodayAttendance() {
        try {
            const formattedDate = this.formattedDate(this.state.dateToday)
            const attendance = await this.orm.searchCount('mz.attendance.student', [
                ['course_id', '=', this.state.slideChanel],
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
        const values = beneficiariesStudents.map(b => this.prepareValuesForCreate(b, this.state.slideChanel, this.state.dateToday))
        
        try {
            await this.orm.create('mz.attendance.student', values);
            this.state.isAttendanceSubmitted = true
            const date = this.state.dateToday
            const msg = `La asistencia del día ${date} ha sido registrada correctamente.`
            this.displayNotification(msg)
        } catch (error) {
            // const date = this.state.dateToday
            // const msg = `La asistencia del día ${date} ha sido registrada correctamente.`
            // this.displayNotification(msg)
            console.error("Error al guardar las asistencias:", error);
        }
    }

    prepareValuesForCreate(beneficiary, course, date) {
        let attendance = beneficiary.attendance ? 'present' : 'absent';
        let subState = attendance === 'absent' ? (beneficiary.justified ? 'jst' : 'wjst') : 'na';
    
        const formattedDate = this.formattedDate(date)
        return {
            'student_id': beneficiary.student_id,
            'course_id': course,
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
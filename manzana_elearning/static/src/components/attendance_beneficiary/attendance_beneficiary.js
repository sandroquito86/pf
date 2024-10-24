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
        this.state = useState({
            slideChanel : this.env.model.root.evalContext.id,
            beneficiaries : [],
            attend: false,
            dateToday: DateTime.local().toFormat('dd/MM/yyyy'),
            date: luxon.DateTime.now(),
            today: luxon.DateTime.now(),
        });

        onMounted(async ()=>{
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
            return JSON.parse(configs)
        } catch (error) {
            console.error("Error en la llamada RPC:", error);
        }
    }

    handleClick() {
        console.log('Clic en el componente de Asistencias');
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

    async saveAttendances() {
        const beneficiariesStudents = this.state.beneficiaries.filter(b => b.student_id)
        const values = beneficiariesStudents.map(b => this.prepareValuesForCreate(b, this.state.slideChanel, this.state.dateToday))
        
        try {
            await this.orm.create('mz.attendance.student', values);
        } catch (error) {
            console.error("Error al guardar las asistencias:", error);
        }
    }

    prepareValuesForCreate(beneficiary, course, date) {
        let attendance = beneficiary.attendance ? 'present' : 'absent';
        let subState = attendance === 'absent' ? (beneficiary.justified ? 'jst' : 'wjst') : 'na';
    
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
    
        const formattedDate = dateObj.toISOString().split('T')[0];
        return {
            'student_id': beneficiary.student_id,
            'course_id': course,
            'date': formattedDate,
            'state': attendance,
            'sub_state': subState
        };
    }
}

AttendanceBeneficiary.template = "manzana_elearning.attendance_beneficiary";
AttendanceBeneficiary.components = { DatePicker: DateTimePicker, DateTimeInput, CheckBox };

export const attendanceBeneficiary = {
    component: AttendanceBeneficiary
};
registry.category("view_widgets").add("mze_attendance_beneficiary", attendanceBeneficiary);
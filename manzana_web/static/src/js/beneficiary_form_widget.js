/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

var BeneficiaryForm = publicWidget.Widget.extend({
    start: function () {
        var self = this;
        const post = this._getPost();
        var res = this._super.apply(this.arguments).then(function () {
            $('#beneficiary_form .a-submit')
                .off('click')
                .click(function (ev) {
                    self.on_click(ev);
                });

            // Agregar validación en tiempo real para correo y cédula
            $('#beneficiary_form input[name="email"]').on('blur', function() {
                self._validateEmail($(this));
            });

            $('#beneficiary_form input[name="numero_documento"]').on('blur', function() {
                if ($('#beneficiary_form select[name="tipo_documento"]').val() === 'dni') {
                    self._validateCedula($(this));
                }
            });

            // Validar cédula solo cuando el tipo de documento es DNI
            $('#beneficiary_form select[name="tipo_documento"]').on('change', function() {
                const $cedula = $('#beneficiary_form input[name="numero_documento"]');
                if ($(this).val() === 'dni') {
                    self._validateCedula($cedula);
                } else {
                    self._removeError($cedula);
                }
            });
        });
        return res;
    },

    _getPost: function () {
        var post = {};
        $('#beneficiary_form input, #beneficiary_form select').each(function () {
            post[$(this).attr('name')] = $(this).val();
        });
        return post;
    },

    /**
     * Valida el formulario completo
     * @private
     * @returns {Boolean}
     */
    _validateForm: function() {
        var isValid = true;
        var self = this;

        // Limpiar errores previos
        this._clearAllErrors();

        // Validar campos requeridos
        $('#beneficiary_form input[required], #beneficiary_form select[required]').each(function() {
            if (!$(this).val()) {
                isValid = false;
                self._addError($(this), "Este campo es requerido");
            }
        });

        // Validar email
        const $email = $('#beneficiary_form input[name="email"]');
        if ($email.val() && !this._validateEmail($email)) {
            isValid = false;
        }

        // Validar cédula si el tipo de documento es DNI
        const $tipoDoc = $('#beneficiary_form select[name="tipo_documento"]');
        const $cedula = $('#beneficiary_form input[name="numero_documento"]');
        if ($tipoDoc.val() === 'dni' && !this._validateCedula($cedula)) {
            isValid = false;
        }

        return isValid;
    },

    /**
     * Valida el formato de email y muestra error si es inválido
     * @private
     * @param {jQuery} $field
     * @returns {Boolean}
     */
    _validateEmail: function($field) {
        const email = $field.val();
        const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
        
        if (!email) {
            return true; // Si está vacío, la validación de required se encargará
        }

        if (!emailRegex.test(email)) {
            this._addError($field, "Por favor ingrese un correo electrónico válido");
            return false;
        }

        this._removeError($field);
        return true;
    },

    /**
     * Valida cédula ecuatoriana
     * @private
     * @param {jQuery} $field
     * @returns {Boolean}
     */
    _validateCedula: function($field) {
        const cedula = $field.val();

        if (!cedula) {
            return true; // Si está vacío, la validación de required se encargará
        }

        // Validar longitud
        if (cedula.length !== 10) {
            this._addError($field, "La cédula debe tener 10 dígitos");
            return false;
        }

        // Validar que solo contenga números
        if (!/^\d+$/.test(cedula)) {
            this._addError($field, "La cédula solo debe contener números");
            return false;
        }

        // Algoritmo de validación de cédula ecuatoriana
        try {
            const provincia = parseInt(cedula.substring(0, 2));
            if (provincia < 1 || provincia > 24) {
                this._addError($field, "Código de provincia inválido");
                return false;
            }

            const tercerDigito = parseInt(cedula.charAt(2));
            if (tercerDigito > 6) {
                this._addError($field, "Tercer dígito inválido");
                return false;
            }

            // Algoritmo de verificación
            const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
            let suma = 0;

            for (let i = 0; i < 9; i++) {
                let valor = parseInt(cedula.charAt(i)) * coeficientes[i];
                suma += valor > 9 ? valor - 9 : valor;
            }

            const digitoVerificador = suma % 10 ? 10 - (suma % 10) : 0;
            
            if (digitoVerificador !== parseInt(cedula.charAt(9))) {
                this._addError($field, "Número de cédula inválido");
                return false;
            }

            this._removeError($field);
            return true;

        } catch (e) {
            this._addError($field, "Número de cédula inválido");
            return false;
        }
    },

    /**
     * Agrega mensaje de error a un campo
     * @private
     * @param {jQuery} $field
     * @param {String} message
     */
    _addError: function($field, message) {
        this._removeError($field);
        $field.addClass('is-invalid');
        $('<div>', {
            class: 'invalid-feedback',
            text: message
        }).insertAfter($field);
    },

    /**
     * Remueve mensaje de error de un campo
     * @private
     * @param {jQuery} $field
     */
    _removeError: function($field) {
        $field.removeClass('is-invalid');
        $field.next('.invalid-feedback').remove();
    },

    /**
     * Limpia todos los mensajes de error
     * @private
     */
    _clearAllErrors: function() {
        $('#beneficiary_form .is-invalid').removeClass('is-invalid');
        $('#beneficiary_form .invalid-feedback').remove();
    },

    on_click: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        
        if (!this._validateForm()) {
            return false;
        }

        var $form = $(ev.currentTarget).closest('form');
        var $button = $(ev.currentTarget).closest('[type="submit"]');
        const post = this._getPost();
        $button.attr('disabled', true);
        return $form.submit();
    },
});

publicWidget.registry.BeneficiaryFormInstance = publicWidget.Widget.extend({
    selector: '#beneficiary_form',
    start: function () {
        var def = this._super.apply(this, arguments);
        this.instance = new BeneficiaryForm(this);
        return Promise.all([def, this.instance.attachTo(this.$el)]);
    },
});

export default BeneficiaryForm;
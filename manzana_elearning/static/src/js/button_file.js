/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { session } from "@web/session";

publicWidget.registry.FileUploadWidget = publicWidget.Widget.extend({
    selector: '.file-download-container, .file-upload-container, .icon-upload-succes',
    
    start: function () {
        this.assignmentId = this.$el.data('assignment-id');
        this.userId = session.user_id;
        this.isPastDeadline = this.$el.data('is-past-deadline') === 'True';
        console.log(this.isPastDeadline)
        this._bindEvents();
        return this._super.apply(this, arguments);
    },

    _bindEvents: function() {
        if (!this.isPastDeadline) {
            this.$el.on('click', '.file-upload-icon', this._onClickUpload.bind(this));
            this.$el.on('change', 'input[type="file"]', this._onFileSelected.bind(this));
            this.$el.on('click', '.delete-icon', this._onClickFileDelete.bind(this));
        }
        this.$el.on('click', '.file-name, .fa-download', this._onClickDownload.bind(this));
    },

    _onClickUpload: function (ev) {
        ev.preventDefault();
        if (this.isPastDeadline) {
            this._showMessage('El plazo para subir la tarea ha vencido', 'warning');
            return;
        }
        this.$('input[type="file"]').click();
    },

    _onFileSelected: function (ev) {
        if (this.isPastDeadline) {
            this._showMessage('El plazo para subir la tarea ha vencido', 'warning');
            return;
        }
        var file = ev.target.files[0];
        if (file) {
            this._uploadFile(file);
        }
    },

    _onClickDownload: function (ev) {
        ev.preventDefault();
        const $downloadLink = this.$('a[href^="/web/content/"]');
        if ($downloadLink.length) {
            window.location.href = $downloadLink.attr('href');
        } else {
            console.error("No se encontró el enlace de descarga");
        }
    },

    _onClickFileDelete: function (ev) {
        ev.preventDefault();
        if (this.isPastDeadline) {
            this._showMessage('No se puede eliminar la tarea después de la fecha límite', 'warning');
            return;
        }
        console.log("Delete icon clicked");
        const studentAssignmentId = $(ev.currentTarget).data('student-assignment-id');
        if (confirm('¿Estás seguro de que quieres eliminar esta tarea?')) {
            this._deleteFile(studentAssignmentId);
        }
    },

    _deleteFile: function(studentAssignmentId) {
        if (this.isPastDeadline) {
            this._showMessage('No se puede eliminar la tarea después de la fecha límite', 'warning');
            return;
        }
        var self = this;
        $.ajax({
            url: '/delete/assignment/' + studentAssignmentId,
            type: 'POST',
            data: {
                'assignment_id': this.assignmentId,
                'student_assignment_id': studentAssignmentId,
                'user_id': this.userId,
                'csrf_token': odoo.csrf_token,
            },
            success: function (response) {
                var result = JSON.parse(response);
                if (result.success) {
                    self._showMessage('Tarea eliminada con éxito', 'success');
                    self._updateUIAfterDelete();
                } else {
                    self._showMessage(result.error || 'Error al eliminar la tarea', 'error');
                }
            },
            error: function (xhr, status, error) {
                self._showMessage('Error al eliminar la tarea: ' + error, 'error');
                console.log(xhr.responseText);
            }
        });
    },

    _uploadFile: function (file) {
        if (this.isPastDeadline) {
            this._showMessage('El plazo para subir la tarea ha vencido', 'warning');
            return;
        }

        var self = this;
        var formData = new FormData();
        formData.append('submitted_file', file);
        formData.append('assignment_id', this.assignmentId);
        formData.append('user_id', this.userId);
        console.log(file)
        console.log(this.userId)

        $.ajax({
            url: '/submit/assignment/' + this.assignmentId,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                var result = JSON.parse(response);
                if (result.success) {
                    const assignment = result.assignment[0];
                    self._showMessage('Tarea subida con éxito', 'success');
                    console.log("Calling _updateUI with:", assignment);
                    self._updateUI(assignment.filename, assignment.id);
                } else {
                    self._showMessage(result.error || 'Error al subir la tarea', 'error');
                }
            },
            error: function (xhr, status, error) {
                self._showMessage('Error al subir la tarea: ' + error, 'error');
            }
        });
    },

    _updateUI: function (fileName, studentAssignmentId) {
        console.log("_updateUI called with:", fileName, studentAssignmentId);

        const newHTML = `
            <div class="o_field_widget o_required_modifier o_field_binary file-download-container" data-assignment-id="${this.assignmentId}">
                <label class="btn btn-sm btn-link p-0">
                    <span class="file-name">${fileName}</span>
                
                <a href="/web/content/mz.student.assignments/${studentAssignmentId}/submitted_file?download=true" class="btn btn-sm btn-secondary"
                    style="background-color: transparent;border-color: transparent; color: inherit;">
                    <i class="fa fa-download" style="color:#243742;"></i>
                </a>
                </label>
                <span class="fa fa-trash btn btn-sm delete-icon" data-student-assignment-id="${studentAssignmentId}"></span>
            </div>
        `;

        //console.log("New HTML to be inserted:", newHTML);

        // Actualizar el contenido del elemento existente en lugar de reemplazarlo
        this.$el.html(newHTML);

        // const elemento = this.$el.closest('.o_wslides_slides_list_slide_controls')
        // console.log(elemento)
        // const subElmento = elemento.find('.o_wslides_slide_completed')
        // console.log(subElmento)
        // .addClass('text-success');

        //console.log("UI updated with new HTML");
        //console.log("Updated DOM structure:", this.$el.prop('outerHTML'));
    },

    _updateUIAfterDelete: function () {
        const newHTML = `
            <div id="file_upload_ui" class="o_field_widget o_required_modifier o_field_binary file-upload-container" data-assignment-id="${this.assignmentId}">
                <label class="o_select_file_button btn btn-sm btn-link p-0">
                    <span class="file-upload-icon" style="display:contents">
                        <i class="fa fa-upload fa-fw"></i>
                    </span>
                    <span class="upload-text">Subir tarea</span>
                    <span class="file-name-display ms-2"></span>
                    <input type="file" class="o_input_file d-none" id="submitted_file_${this.assignmentId}" name="submitted_file_${this.assignmentId}" required="required"/>
                </label>
            </div>
        `;

        this.$el.html(newHTML);
    },

    _showMessage: function (message, type) {
        console.log(type + ': ' + message);
        // Implementa aquí la lógica para mostrar mensajes al usuario
    }
});

export default publicWidget.registry.FileUploadWidget;
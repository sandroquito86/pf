/** @odoo-module **//** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.EventsAssignmentWidget = publicWidget.Widget.extend({
        selector: '.event-assignment-container',
        events: {
            'click .show-assignment-details': '_onShowAssignmentDetails',
        },

        start: function () {
            this.assignmentId = this.$el.data('assignment-id');
            console.log('pppppppppp')
            this.assignmentName = this.$el.data('assignment-name');
            this.assignmentDescription = this.$el.data('assignment-description');
            this.assignmentDueDate = this.$el.data('assignment-due-date');
            return this._super.apply(this, arguments);
        },


        _onShowAssignmentDetails: function (ev) {
            ev.preventDefault();
            console.log('AAAA')
            this._showAssignmentDetailsModal();
        },


        _showAssignmentDetailsModal: function () {
            var $modal = this._getModal();
            var $modalBody = $modal.find('.modal-body');
            
            // Limpiar el contenido anterior
            $modalBody.empty();
            
            // Añadir los detalles de la tarea
            $modalBody.append($('<h4>').text(this.assignmentName));
            $modalBody.append($('<p>').text(this.assignmentDescription));
            if (this.assignmentDueDate) {
                $modalBody.append($('<p>').text(_t("Due Date: ") + this.assignmentDueDate));
            }
            
            // Mostrar el modal
            $modal.modal('show');
        },


        _getModal: function () {
            var $modal = $('#assignmentDetailsModal');
            if ($modal.length === 0) {
                $modal = $(qweb.render('mz_elearning.AssignmentDetailsModal'));
                $modal.appendTo('body');
            }
            return $modal;
        },


    });

export default publicWidget.registry.EventsAssignmentWidget;
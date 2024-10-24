odoo.define('your_module.date_field_widget', function (require) {
    "use strict";

    var core = require('web.core');
    var basicFields = require('web.basic_fields');
    var registry = require('web.field_registry');

    var DateWidget = basicFields.DateWidget.extend({
        start: function () {
            this._super.apply(this, arguments);
            this.$input.attr('min', moment().format('YYYY-MM-DD'));
        },
    });

    registry.add('date', DateWidget);

    return DateWidget;
});
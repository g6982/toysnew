odoo.define('aspl_pos_close_session.models', function (require) {
"use strict";

    var models = require('point_of_sale.models');

    models.load_fields("res.users", ['display_amount_during_close_session']);
});

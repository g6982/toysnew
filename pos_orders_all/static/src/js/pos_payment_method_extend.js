odoo.define('pos_orders_all.pos_payment_method_extend', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    var _super_posmodel = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend(
    {
        initialize: function (session, attributes) {
            var session_model = _.find(this.models, function(model){ return model.model === 'pos.payment.method'; });
            session_model.fields.push('is_refund');
            return _super_posmodel.initialize.call(this, session, attributes);
        },

    });
});


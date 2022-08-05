odoo.define('pos_orders_all.pos_payment_extend', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var SuperPaymentline = models.Paymentline.prototype;

    var _super_posmodel = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend(
    {
        initialize: function (session, attributes) {
            var session_model = _.find(this.models, function(model){ return model.model === 'pos.payment'; });
            session_model.fields.push('pos_order_id','partner_id','pos_reference','date_order','is_used','credit_client');
            return _super_posmodel.initialize.call(this, session, attributes);
        },

    });


     models.Paymentline = models.Paymentline.extend({
        initialize: function () {
            SuperPaymentline.initialize.apply(this, arguments);
            this.payments_refund = [];
       },

       export_as_JSON: function () {
            var Payment = SuperPaymentline.export_as_JSON.apply(this, arguments);
            Payment.payments_refund = this.payments_refund

            return Payment;
        },
    });

});


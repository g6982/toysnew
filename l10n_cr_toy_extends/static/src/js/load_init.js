/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('l10n_cr_toy_extends.loads_init', function(require) {
    "use strict";
    var pos_orders = require('pos_orders.pos_orders');
    var core = require('web.core');
    var QWeb = core.qweb;
    var models = require('point_of_sale.models');
    var SuperOrder = models.Order;
    var SuperOrderline = models.Orderline.prototype;
    var SuperPosModel = models.PosModel.prototype;
    var SuperPaymentline = models.Paymentline.prototype;
    var utils = require('web.utils')
    var round_pr = utils.round_precision;
    const Registries = require('point_of_sale.Registries');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const NumpadWidget = require('point_of_sale.NumpadWidget');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const { posbus } = require('point_of_sale.utils');

    models.load_models([{
        model: 'pos.payment',
        fields: ['id', 'name', 'payment_method_id', 'amount','partner_id','pos_reference','is_used','credit_client'],
        loaded: function(self, payments) {
            self.db.all_payments_jhonny = payments;
            self.db.payment_by_jhonny_id = {};
            payments.forEach(function(payment) {
                self.db.payment_by_jhonny_id[payment.id] = payment;
                self.db.payment_by_jhonny_id[payment.id]['journal_id'] = payment.payment_method_id
                self.db.payment_by_jhonny_id[payment.id]['partner_id'] = payment.partner_id
                delete self.db.payment_by_jhonny_id[payment.id]['payment_method_id']
            });
        },
    }]);

    models.load_fields('pos.payment.method', ['is_card','is_transfer']);

    models.Paymentline = models.Paymentline.extend({
        initialize: function () {
            SuperPaymentline.initialize.apply(this, arguments);
            this.complete_data = false;
        },

         set_complete_data: function(value){
            this.complete_data = value
         }

     });

});
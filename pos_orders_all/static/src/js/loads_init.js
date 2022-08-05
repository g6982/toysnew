/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_orders_all.loads_init', function(require) {
    "use strict";
    var pos_orders = require('pos_orders.pos_orders');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
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

    models.load_fields('pos.payment.method', ['is_refund']);
    models.load_models([{
        model: 'pos.payment',
        fields: ['id', 'name', 'payment_method_id', 'amount','partner_id','pos_reference','is_used','credit_client','amount_used','create_date'],
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


     models.PosModel = models.PosModel.extend({
        _save_to_server: function (orders, options) {
            var self = this;
            return SuperPosModel._save_to_server.call(this,orders,options).then(function(return_dict){
                if(return_dict){
                    _.forEach(return_dict, function(data){
                        if(data.orders != null){
                            if(self.db.all_payments_jhonny)
                                data.payments.forEach(function(payment) {
                                    var pay = payment;
                                    pay['pos_reference'] = data.pos_reference;
                                    pay['partner_id'] = data.orders[0].partner_id
                                    pay['date_order'] = data.orders[0].date_order;
                                    pay['is_used'] = false;
                                    if( data.orders[0].amount_total < 0 && pay.amount < 0){
                                        pay['credit_client'] = true;
                                    }else{
                                        pay['credit_client'] = false;
                                    }

                                    self.match_credits_payment();

                                    self.db.all_payments_jhonny.unshift(pay);
                                    self.db.payment_by_jhonny_id[payment.id] = payment;


                            });

                             if (data.payments.length == 0 && data.orders[0].amount_total < 0) {
                                rpc.query({
                                    model: 'res.partner',
                                    method: 'get_pos_payment_by_client',
                                    args: [[data.orders[0].partner_id[0]]],
                                })
                                .then(function(pago){
                                    self.db.all_payments_jhonny.unshift(pago);
                                }).guardedCatch(function(){
                                    console.log("No se encontró resultados.")
                                });

                            }

                            delete data.payments;


                        }
                    })
                }
                return return_dict
            });
        },

        match_credits_payment: function(){
            var order = this.attributes.selectedOrder;
            if(order.selected_paymentline != undefined){
                if(order.selected_paymentline.payments_refund.length > 0){
                    for(var i=0; i < order.selected_paymentline.payments_refund.length; i++){
                        var all_payments_jhonny = this.db.all_payments_jhonny;
                        for(var j=0; j<all_payments_jhonny.length; j++){
                            if(all_payments_jhonny[j].id ==  order.selected_paymentline.payments_refund[i].id ){
                                all_payments_jhonny[j].is_used = true;
                            }
                        }
                    }
                }

            }
        }
    });

});
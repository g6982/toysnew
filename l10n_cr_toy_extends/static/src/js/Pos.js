// pos_orders_all js
odoo.define('l10n_cr_toy_extends.Pos', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	const PaymentScreen = require('point_of_sale.PaymentScreen');
	var SuperPaymentline = models.Paymentline.prototype;
	var PosDB = require("point_of_sale.DB");
	var utils = require('web.utils');
	var round_pr = utils.round_precision;


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



    var posorder_super = models.Order.prototype;
	models.Order = models.Order.extend({
		initialize: function(attr, options) {
			this.coupon_code = this.coupon_code || false;
			this.note = this.note || false;
			//this.saldo = this.saldo || false;
			posorder_super.initialize.call(this,attr,options);
		},

		set_coupon_code: function(coupon_code){
			this.coupon_code = coupon_code;
			this.trigger('change',this);
		},

		get_coupon_code: function(coupon_code){
			return this.coupon_code;
		},

		set_note: function(note){
			this.note = note;
			this.trigger('change',this);
		},

		get_note: function(note){
			return this.note;
		},

//        set_saldo: function(saldo){
//			this.saldo = saldo;
//			this.trigger('change',this);
//		},
//
//		get_saldo: function(saldo){
//			return this.saldo;
//		},


		export_as_JSON: function() {
		    var self = this;
			var loaded = posorder_super.export_as_JSON.apply(this, arguments);
			loaded.coupon_code = self.coupon_code || false;
			loaded.note = self.note || false;
			return loaded;
		},

		init_from_JSON: function(json){
			posorder_super.init_from_JSON.apply(this,arguments);
			this.coupon_code = json.coupon_code || false;
			this.note = json.note || false;
		},

//		export_for_printing: function () {
//            var result = posorder_super.export_for_printing.apply(this, arguments);
//            result.saldo = this.get_saldo();
//            return result;
//        },

	});

	var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        export_for_printing: function() {
            var line = _super_orderline.export_for_printing.apply(this,arguments);
            line.producto = this.get_product();
            return line;
        },
    });


    var _super_product = models.Product.prototype;
    models.Product = models.Product.extend({

//          initialize: function(attr, options){
//             this.include_tax_in_price = false;
//             _super_product.initialize.call(this,attr,options);
//          },
          get_price_include_tax: function(pricelist, quantity, price_extra){
            var self = this;

            //si no tiene la opción actica para mostrar impuestos incluidos en los precios continúa normal
            if (self.pos.config.include_tax_in_product == false){
                return _super_product.get_price.apply(this,arguments);
            }

            var date = moment().startOf('day');

            // In case of nested pricelists, it is necessary that all pricelists are made available in
            // the POS. Display a basic alert to the user in this case.
            if (pricelist === undefined) {
                alert(_t(
                    'An error occurred when loading product prices. ' +
                    'Make sure all pricelists are available in the POS.'
                ));
            }

            var category_ids = [];
            var category = this.categ;
            while (category) {
                category_ids.push(category.id);
                category = category.parent;
            }

            var pricelist_items = _.filter(pricelist.items, function (item) {
                return (! item.product_tmpl_id || item.product_tmpl_id[0] === self.product_tmpl_id) &&
                       (! item.product_id || item.product_id[0] === self.id) &&
                       (! item.categ_id || _.contains(category_ids, item.categ_id[0])) &&
                       (! item.date_start || moment(item.date_start).isSameOrBefore(date)) &&
                       (! item.date_end || moment(item.date_end).isSameOrAfter(date));
            });

            var taxes = self.taxes_id;
            var amount_tax = 0;
            if (taxes){
                for(var i=0; i<taxes.length; i++){
                    var tax = self.pos.taxes_by_id[taxes[i]];
                    var amount = this.get_amount_tax(tax,self.lst_price, true);
                    if (amount != false){
                        amount_tax += amount;
                    }


                }

            }

            if (amount_tax > 0){
                var price = self.lst_price + amount_tax;
            }else{
                var price = self.lst_price;
            }


            if (price_extra){
                price += price_extra;
            }
            _.find(pricelist_items, function (rule) {
                if (rule.min_quantity && quantity < rule.min_quantity) {
                    return false;
                }

                if (rule.base === 'pricelist') {
                    price = self.get_price(rule.base_pricelist, quantity);
                } else if (rule.base === 'standard_price') {
                    price = self.standard_price;
                }

                if (rule.compute_price === 'fixed') {
                    price = rule.fixed_price;
                    return true;
                } else if (rule.compute_price === 'percentage') {
                    price = price - (price * (rule.percent_price / 100));
                    return true;
                } else {
                    var price_limit = price;
                    price = price - (price * (rule.price_discount / 100));
                    if (rule.price_round) {
                        price = round_pr(price, rule.price_round);
                    }
                    if (rule.price_surcharge) {
                        price += rule.price_surcharge;
                    }
                    if (rule.price_min_margin) {
                        price = Math.max(price, price_limit + rule.price_min_margin);
                    }
                    if (rule.price_max_margin) {
                        price = Math.min(price, price_limit + rule.price_max_margin);
                    }
                    return true;
                }

                return false;
            });

            // This return value has to be rounded with round_di before
            // being used further. Note that this cannot happen here,
            // because it would cause inconsistencies with the backend for
            // pricelist that have base == 'pricelist'.
            return price;
        },

        get_amount_tax: function(tax,base_amount,price_exclude){
            if(price_exclude === undefined)
                var price_include = tax.price_include;
            else
                var price_include = !price_exclude;
            if (tax.amount_type === 'fixed') {
                var sign_base_amount = Math.sign(base_amount) || 1;
                // Since base amount has been computed with quantity
                // we take the abs of quantity
                // Same logic as bb72dea98de4dae8f59e397f232a0636411d37ce
                return tax.amount * sign_base_amount * Math.abs(quantity);
            }
            if (tax.amount_type === 'percent' && !price_include){
                return base_amount * tax.amount / 100;
            }
            if (tax.amount_type === 'percent' && price_include){
                return base_amount - (base_amount / (1 + tax.amount / 100));
            }
            if (tax.amount_type === 'division' && !price_include) {
                return base_amount / (1 - tax.amount / 100) - base_amount;
            }
            if (tax.amount_type === 'division' && price_include) {
                return base_amount - (base_amount * (tax.amount / 100));
            }
            return false;

        }
    });




});
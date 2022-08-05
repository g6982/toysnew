odoo.define('l10n_cr_toy_extends.CouponPromotion', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const ProductScreen = require('point_of_sale.ProductScreen');
	const { useListener } = require('web.custom_hooks');
	const Registries = require('point_of_sale.Registries');
	const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    var rpc = require('web.rpc');

	class CouponPromotionButton extends PosComponent {
		constructor() {
			super(...arguments);
			useListener('click', this.onClick);
		}
		async onClick() {
		    let self = this;
			let order = self.env.pos.get_order();
		    this.showPopup('CouponPromotionPopup', {
                coupon: order.coupon_code ? order.coupon_code : "",
                exist_coupon: order.coupon_code ? 1 : 0
            });
		}
	}
	CouponPromotionButton.template = 'CouponPromotionButton';


	ProductScreen.addControlButton({
		component: CouponPromotionButton,
		condition: function() {
			return true;
		},
	});


	Registries.Component.add(CouponPromotionButton);


	class CouponPromotionPopup extends AbstractAwaitablePopup {

		constructor() {
            super(...arguments);
            // this.renderElement();
        }

        cancel(){
			this.trigger('close-popup')
		}

		async remove_coupon(){
		    let self = this;
		    var order = self.env.pos.get_order();
		    var lines = order.orderlines.models;

		    var input = $(".code_coupon_class")[0];

            for(var i=0; i < lines.length; i++){
                lines[i].set_discount(0);
                lines[i].trigger('change', lines[i]);
            }

            order.set_coupon_code("");
            order.set_note("")

            input.value = "";

            self.cancel();
		}

        async apply_coupon(){

            let self = this;

        	var order = self.env.pos.get_order();
        	let coupon_code = $(".code_coupon_class")[0].value;

        	if(coupon_code=="" || coupon_code==undefined || !coupon_code){
        	     swal("Ups !", "Ingrese por favor el código de cupón o promoción", "warning")
                 return 0;
        	}

			if(order){
			    var lineas = [];
			    var l = order.orderlines.models;
			    for(var i=0; i < l.length; i++){
			        lineas.push({
			            'full_product_name': l[i].full_product_name,
			            'product_id': l[i].product.id,
			            'price_unit': l[i].price,
			            'discount': l[i].discount,
			            'qty': l[i].quantity,
			        })
			    }


			    let dict ={
						'company_id': order.pos.company.id,
						'session_id': self.env.pos.pos_session.id,
						'partner_id': order.changed.client ? order.changed.client.id : false,
						'pricelist_id': order.pricelist.id,
						'name': order.name,
						'lines': lineas,
						'uid': order.uid,
						'amount_total': order.validation_date,
						'amount_tax': 0.0,
						'amount_paid': 0.0,
						'amount_return': 0.0,
						'config_id': order.pos.config_id,
					}


				await rpc.query({
                   model: 'pos.order',
                   method: 'create_provisional_order',
                   args: [dict, coupon_code],
                }, {
                    shadow: true,
                }).then(function (res) {

                    var o = res[0];
                    var t = res[1];
                    if(o.length > 0){
                        var order = self.env.pos.get_order();
                        var lines = order.orderlines.models;
                        var price_subtotal_incl = 0.0;
                        for(var y=0; y < o.length; y++){
                            price_subtotal_incl = price_subtotal_incl + o[y]['price_subtotal_incl']
                        }

                        var percentage = (price_subtotal_incl * 100) / t[0];
                        //var percentage_by_line = (percentage / lines.length).toFixed(2);

                        for(var i=0; i < lines.length; i++){
                            lines[i].set_discount(Math.abs(percentage).toFixed(2));
                            lines[i].trigger('change', lines[i]);
                        }

                        console.log("Cupón " + $(".code_coupon_class")[0].value);
                        order.set_coupon_code($(".code_coupon_class")[0].value);
                        order.set_note(o[0].full_product_name)

                        self.cancel();
                    }
                    else{
                        self.cancel();
                    }

                });
			}

        }
	};

    CouponPromotionPopup.template = 'CouponPromotionPopup';
    Registries.Component.add(CouponPromotionPopup);

});

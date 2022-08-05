odoo.define('l10n_cr_toy_extends.PosOrdersAll', function (require) {
	'use strict';
    var core = require('web.core');
	const pos_orders = require('pos_orders.pos_orders');
	const Registries = require('point_of_sale.Registries');
	const {useState} = owl.hooks;
	const {useListener} = require('web.custom_hooks');

	const ToysPOSOrdersScreen = (pos_orders) =>
        class extends pos_orders{
			constructor() {
				super(...arguments);
                var self = this;
				setTimeout(function(){
				    $('.wk-order-line').on('click', '.view-order', function(event) {
                        self.line_select(event, $(this.parentElement), parseInt($(this).data('id')));
                    });

                     $('.wk-order-line').on('click', '.print-order', function(event) {
                        self.clickReprint(event, parseInt($(this).data('id')));
                    });

                    var contents = $('.order-details-contents');
                    contents.empty();
                    var parent = $('.wk_order_list').parent();
                    parent.scrollTop(0);
				},150);
				useListener('click-reprint', this.clickReprint);
				useListener('click-detail', this.clickDetail);
			}

			async clickReprint(event, order_id){
				let self = this;
				let order = event.detail;

				await self.rpc({
					model: 'pos.order',
					method: 'print_pos_receipt',
					args: [order_id],
				}).then(function(output) {
					let data = output;
					data['order'] = order;
					//self.showTempScreen('OrderReprintScreen',data);
					self.showScreen('OrderReprintScreenToys',data);
					//self.showScreen('OrderReprintScreen',data);
				});

			}

			async clickDetail(event){
			    var self = this;
			    setTimeout(function(){
					self.line_select(event, $(this), order.id);
                    var contents = $('.order-details-contents');
                    contents.empty();
                    var parent = $('.wk_order_list').parent();
                    parent.scrollTop(0);
				},150);
			}
		}

	Registries.Component.extend(pos_orders, ToysPOSOrdersScreen);

});



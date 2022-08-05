odoo.define('bi_pos_warehouse_management.ActionpadWidget', function(require) {
	"use strict";

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	let rpc = require('web.rpc');
	const { useListener } = require('web.custom_hooks');
	const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
	const { useState } = owl.hooks;
	const ProductScreen = require('point_of_sale.ProductScreen'); 

	const BiProductScreen = (ProductScreen) =>
	class extends ProductScreen {
		constructor() {
			super(...arguments);
		}

		async _clickProduct(event) { 
			var self = this;
			const product = event.detail;
			let location = self.env.pos.config.stock_location_id;
			let partner_id = self.env.pos.get_client();
			let other_locations = self.env.pos.pos_custom_location;
			let product_id = product['id'];
			let call_super = false;
			let result = 0;
			let has_qty = false;
			// Deny POS Order When Product is Out of Stock
			if (product.type == 'product'  && self.env.pos.config.display_stock_pos)
			{
				await this.rpc({
					model: 'stock.quant',
					method: 'get_product_stock',
					args: [partner_id, location, other_locations, product_id],
				}).then(function(output) {
					if (output[0] <= 0)
					{	
						result = output[1];
					}
					else {
						has_qty = true;
						call_super = true;
					}
				});
				if(!has_qty){
					const { confirmed } = await this.showPopup('ConfirmPopup', {
						title: this.env._t('Out of Stock !!'),
						body: this.env._t('The product you have selected is out of stock'),
						cancelText: this.env._t('Cancel'),
						confirmText: this.env._t('CheckAvailability'),
						'product': product, 
						'result':result,
					});
					if (confirmed) {
						self.showPopup('PosStockWarehouse', {
							'product': product,
							'result': result,
						});
					}else {
						call_super = false;
					}	
				}
				
			}else {
				call_super = true;
			}

			if(call_super == true){
				super._clickProduct(event);
			}
		}

		_onClickPay() {
			let self = this;
			let order = self.env.pos.get_order();
			let orderlines = order.get_orderlines();
			let products = {};
			let prods = [];
			let call_super = true;
			let rpc_result = false;
			if(orderlines.length > 0 && self.env.pos.config.display_stock_pos){
				orderlines.forEach(function (line) {
					let prod = line.product;
					let loc = line.stock_location_id;
					if(prod.type == 'product' ){
						if(loc){
							prods.push(prod.id)
							if(products[prod.id] == undefined){
								products[prod.id] =  [{ 'loc' :loc,
								'line' : line.id,
								'name': prod.display_name,
								'qty' :parseFloat(line.quantity)}];
							}
							else{
								products[prod.id].forEach(function (val) {
									if(val['loc'] == loc){
										val['qty'] += parseFloat(line.quantity);
									}
									else{
										products[prod.id].push({ 'loc' :loc,
											'line' : line.id,
											'name': prod.display_name,
											'qty' :parseFloat(line.quantity)}) 
									}
								});	
							}	
						}
						else{
							let config_loc = self.env.pos.config.stock_location_id[0];
							rpc_result = rpc.query({
								model: 'stock.quant',
								method: 'get_loc_stock',
								args: [1,config_loc , prod.id],
							},{async:false}).then(function(output) {
								if(line.quantity > output){
									call_super = false;
									self.showPopup('ErrorPopup', {
										title: self.env._t('Out of Stock'),
										body: self.env._t("(" + product.display_name + ")" + " is Out of Stock."),
									});
								}	
							});	
						}
					}
				});	

				$.each(order.order_products, function( key, value ) {
					$.each(products, function( key1, value1 ) {
						if(key === key1) { 
							$.each(value, function( key2, value2 ) {
								$.each(value1, function( key3, value3 ) {
									if(value2['location'] == value3['loc']) {
										if(value2['qty'] < value3['qty']) { 
											order.is_out = true;
											call_super = false;

											self.showPopup('ErrorPopup', {
												title: self.env._t('Out of Stock'),
												body: self.env._t("(" + value2['name'] + ")" + " is Out of Stock."),
											});
										}
									}
								});
							});
						}
					});
				});

			}

			$.when(rpc_result).done(function() {
				if(call_super == true){
					self.showScreen('PaymentScreen');
				}
			});
			
		}

	};

	Registries.Component.extend(ProductScreen, BiProductScreen);

	return ProductScreen;
});
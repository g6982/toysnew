odoo.define('bi_pos_warehouse_management.OrderWidget', function(require) {
	"use strict";

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const { useListener } = require('web.custom_hooks');
	const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
	const { useState } = owl.hooks;
	const rpc = require('web.rpc');
	const OrderWidget = require('point_of_sale.OrderWidget');

	const BiOrderWidget = (OrderWidget) =>
	class extends OrderWidget {
		constructor() {
			super(...arguments);
		}
		
		mounted() {
			// this._super();
			this.order.orderlines.on('change', () => {
				let self = this;
				this.order.orderlines.each(function(line){
					let order = self.order;
					let location = line.stock_location_id;
					let product_id = line.product;
					let odr_prods = {};
					if(order.order_products  == undefined){
						order.order_products = {};
					}
					if(product_id.type == 'product'  && self.env.pos.config.display_stock_pos){
						if(location){
							if(order.order_products[product_id.id] == undefined){
								rpc.query({
									model: 'stock.quant',
									method: 'get_loc_stock',
									args: [1,location , product_id.id],
								},{async:false}).then(function(output) {
									order.order_products[product_id.id] =  [{ 'location' :location,
									'name': product_id.display_name,
									'qty' :parseFloat(output)}];
								});												
							}
							else{
								order.order_products[product_id.id].forEach(function (val) {
									if(val['location'] != location){
										rpc.query({
											model: 'stock.quant',
											method: 'get_loc_stock',
											args: [1,location , product_id.id],
										},{async:false}).then(function(output) {
											order.order_products[product_id.id].push({ 'location' :location,
												'line' : this.id,
												'name': product_id.display_name,
												'qty' :parseFloat(output)}) 
										});	
									}
								});	
							}	
						}
					}
				});
			});
		}
	};

	Registries.Component.extend(OrderWidget, BiOrderWidget);

	return OrderWidget;

});
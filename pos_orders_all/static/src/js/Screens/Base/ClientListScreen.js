odoo.define('pos_orders_all.ClientListScreen', function (require) {
	'use strict';

	const ClientListScreen = require('point_of_sale.ClientListScreen');
	const {useState} = owl.hooks;
	const {useListener} = require('web.custom_hooks');
	const models = require('point_of_sale.models');
	const Registries = require('point_of_sale.Registries');

	const BiClientListScreen = (ClientListScreen) =>
		class extends ClientListScreen {
			constructor() {
				super(...arguments);
				useListener('click-show-orders', this.showOrders);
			}

			async showOrders(event){
				let partner_id = parseInt(event.detail.id);
				await this.showTempScreen('POSOrdersScreen', {
					'selected_partner_id': partner_id 
				});
			}



//			confirm() {
//			    var res = super.confirm()
//			    var a = 1;
//			    return res;
//
//			}
//
//			clickNext() {
//                var res = super.clickNext();
//                if(this.state.selectedClient==null){
//                    if(this.currentOrder.selected_paymentline){
//                         //this.env.bus.trigger('unselect-credit-all');
//                         //this.env.bus.trigger('update-credits-pendings');
//                         this.currentOrder.selected_paymentline.empty_paguitos();
//                         //this.trigger('empty-paguitos');
//                    }
//                }
//                else{
//                    if(this.state.selectedClient && this.props.client==null){
//                         this.currentOrder.selected_paymentline.updateSelectClient();
//                         //this.trigger('update-select-client');
//                    }else{
//                          if(this.state.selectedClient && this.props.client){
//                             this.env.bus.trigger('unselect-credit-all');
//                             this.env.bus.trigger('update-credits-pendings');
//                             this.env.bus.trigger('empty-paguitos');
//                             this.env.bus.trigger('update-select-client');
//                          }
//                    }
//                }
//                return res;
//
//			 }
		}
	Registries.Component.extend(ClientListScreen, BiClientListScreen);

	return ClientListScreen;
});

odoo.define('l10n_cr_toy_extends.OrderReprintScreenToys', function (require) {
	'use strict';

	const ReceiptScreen = require('point_of_sale.ReceiptScreen');
	const Registries = require('point_of_sale.Registries');

	const OrderReprintScreenToys = (ReceiptScreen) => {
		class OrderReprintScreenToys extends ReceiptScreen {
			constructor() {
				super(...arguments);
			}

			back() {
			    this.showScreen('OrdersScreenWidget')
				//this.props.resolve({ confirmed: true, payload: null });
				//this.trigger('close-temp-screen');
			}
		}
		OrderReprintScreenToys.template = 'OrderReprintScreenToys';
		return OrderReprintScreenToys;
	};

	Registries.Component.addByExtending(OrderReprintScreenToys, ReceiptScreen);

	return OrderReprintScreenToys;
});

odoo.define('l10n_cr_toy_extends.OrderReprintReceiptToys', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');

	class OrderReprintReceiptToys extends PosComponent {
		constructor() {
			super(...arguments);
		}

		get receiptBarcode(){
			let barcode = this.props.barcode;
			$("#barcode_print1").barcode(
				barcode, // Value barcode (dependent on the type of barcode)
				"code128" // type (string)
			);
		return true
		}
	}
	OrderReprintReceiptToys.template = 'OrderReprintReceiptToys';

	Registries.Component.add(OrderReprintReceiptToys);

	return OrderReprintReceiptToys;
});
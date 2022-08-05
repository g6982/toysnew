odoo.define('l10n_cr_toy_extends.ProductItem', function (require) {
	'use strict';

	const ProductItem = require('point_of_sale.ProductItem');
	const {useState} = owl.hooks;
	const {useListener} = require('web.custom_hooks');
	const models = require('point_of_sale.models');
	const Registries = require('point_of_sale.Registries');

	const ToysProductItem = (ProductItem) =>
		class extends ProductItem {

			get price() {

			    const formattedUnitPrice = (this.env.pos.config.include_tax_in_product ? (this.env.pos.format_currency(
                        this.props.product.get_price_include_tax(this.pricelist, 1),
                        'Product Price'
                    )) : (this.env.pos.format_currency(
                        this.props.product.get_price(this.pricelist, 1),
                        'Product Price'
                    )) )

                if (this.props.product.to_weight) {
                    return `${formattedUnitPrice}/${
                        this.env.pos.units_by_id[this.props.product.uom_id[0]].name
                    }`;
                } else {
                    return formattedUnitPrice;
                }
            }

		}
	Registries.Component.extend(ProductItem, ToysProductItem);

	return ProductItem;
});

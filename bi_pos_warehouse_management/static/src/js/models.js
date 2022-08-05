// bi_pos_warehouse_management js
odoo.define('bi_pos_warehouse_management.pos', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var session = require('web.session');
	
	models.load_models({
		model: 'stock.location',
		fields: ['name','complete_name'],
		domain: function(self) {
			return [['id', 'in', self.config.warehouse_available_ids]];
		},
		loaded: function(self, pos_custom_location) {
			self.pos_custom_location = pos_custom_location;
		},

	});
	
	var _super_posmodel = models.PosModel.prototype;
	models.PosModel = models.PosModel.extend({
		initialize: function (session, attributes) {
			var product_model = _.find(this.models, function(model){ return model.model === 'product.product'; });
			product_model.fields.push('type','qty_available','incoming_qty','outgoing_qty');
			return _super_posmodel.initialize.call(this, session, attributes);
		},
	});

	var OrderSuper = models.Order;
	models.Order = models.Order.extend({
		init: function(parent,options){
			this._super(parent,options);
			this.order_products = this.order_products || {};
		},

		export_as_JSON: function() {
			var self = this;
			var loaded = OrderSuper.prototype.export_as_JSON.call(this);
			loaded.order_products = self.order_products || {};
			return loaded;
		},

		init_from_JSON: function(json){
			OrderSuper.prototype.init_from_JSON.apply(this,arguments);
			this.order_products = json.order_products || {};
		},
	});

	// exports.Orderline = Backbone.Model.extend ...
	var _super_orderline = models.Orderline.prototype;
	models.Orderline = models.Orderline.extend({
		initialize: function(attr,options){
			_super_orderline.initialize.call(this,attr,options);
			this.stock_location_id = this.stock_location_id || false;
		},

		export_as_JSON: function(){
			var json = _super_orderline.export_as_JSON.call(this);
			json.stock_location_id = this.stock_location_id || false;
			return json;
		},
		init_from_JSON: function(json){
			_super_orderline.init_from_JSON.apply(this,arguments);
			this.stock_location_id = json.stock_location_id || false;
		},
	});

});

# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
from functools import partial
import psycopg2
import pytz


class POSConfigInherit(models.Model):
	_inherit = 'pos.config'
	
	enable_reservation = fields.Boolean('Allow Reserve Order')
	reservation_location = fields.Many2one('stock.location','Location to store reserve products',domain=[('usage', '!=', 'view')])
	cancel_charge_type = fields.Selection([('percentage', "Percentage"), ('fixed', "Fixed")], string='Cancellation Charge Type', default='fixed')
	cancel_charges = fields.Float('Cancellation Charges')
	cancel_charges_product = fields.Many2one('product.product','Cancellation Charges Product',domain=[('type', '=', 'service'),('available_in_pos','=',True)])
	reserve_charge_type = fields.Selection([('percentage', "Percentage"), ('fixed', "Fixed")], string='Reservation Charge Type', default='fixed')
	min_reserve_charges = fields.Float('Minimum amount to reserve order')
	last_days = fields.Integer('Load Reserve Orders for Last')

	def _add_cash_zero(self):
		if self.current_session_id:
			if self.current_session_id.cash_register_id:
				self.current_session_id.cash_register_id.balance_start = 0.0

	def open_session_cb(self, check_coa=True):
		""" new session button

        create one if none exist
        access cash control interface if enabled or start a session
        """
		self.ensure_one()
		self.delete_cache()  # Viene de módulo pos_cache
		if not self.current_session_id:
			self._check_company_journal()
			self._check_company_invoice_journal()
			self._check_company_payment()
			self._check_currencies()
			self._check_profit_loss_cash_journal()
			self._check_payment_method_ids()
			self._check_payment_method_receivable_accounts()
			self.env['pos.session'].create({
				'user_id': self.env.uid,
				'config_id': self.id
			})
			self._add_cash_zero()


		return self.open_ui()
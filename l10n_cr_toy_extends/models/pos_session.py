# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, datetime


class PosSession(models.Model):
    _inherit = 'pos.session'

    def print_report_close_cash(self):
        datas = {'ids': self.id,
                 'model': 'pos.session'
                 }
        return self.env.ref('aspl_pos_close_session.pos_z_report').report_action(self.id)


    def get_amount_total(self):
        amount_total = 0.0
        if self:
            if self.order_ids:
                amount_total = sum(o.amount_total for o in self.order_ids)

        return amount_total

    def get_count_sales(self):
        count = 0
        if self:
            count = len(self.order_ids)

        return count

    def get_cash_in(self):
        cash_in = 0.0
        moves_in = self.env['pos.cash.in.out'].sudo().search([('session_id', '=', self.id),('transaction_type','=','cash_in')])
        if moves_in:
            cash_in = sum(ci.amount for ci in moves_in)

        return cash_in

    def get_cash_out(self):
        cash_out = 0.0
        moves_out = self.env['pos.cash.in.out'].sudo().search([('session_id', '=', self.id), ('transaction_type', '=', 'cash_out')])
        if moves_out:
            cash_out = sum(co.amount for co in moves_out)

        return cash_out

    def get_amount_total_tax(self):
        amount_tax = 0.0
        if self:
            if self.order_ids:
                amount_tax = sum(o.amount_tax for o in self.order_ids)

        return amount_tax

    def get_amount_total_reserved(self):
        amount_paid = 0.0
        if self:
            if self.order_ids:
                o_reserved = self.order_ids.filtered(lambda r:r.state == 'reserved')
                amount_paid = sum(o.amount_paid for o in o_reserved)

        return amount_paid
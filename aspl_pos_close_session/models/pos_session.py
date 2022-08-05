# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from datetime import datetime, date, timedelta
from odoo import models, api, fields, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import json
import pytz
import logging
from pytz import timezone
_logger = logging.getLogger(__name__)

class tableTotalsMethodPaid(models.Model):
    _name = 'method.paid.totals'

    ide= fields.Integer()
    name = fields.Char()
    total = fields.Float()
    session_id = fields.Many2one('pos.session')


class PosSession(models.Model):
    _name = 'pos.session'
    _inherit = 'pos.session'

    cash_register_amount_net = fields.Monetary(compute='_compute_cash_balance_extend',string='Total monto neto',help="Total monto neto de transacciones")
    cash_register_amount_returned = fields.Monetary(compute='_compute_cash_balance_extend',string='Total monto vuelto',help="Total monto de vuelto de transacciones")

    cash_register_total_entry_encoding = fields.Monetary(
        compute='_compute_cash_balance',
        string='Total Cash Transaction',
        readonly=True,
        help="Total of all paid sales orders")

    info_amounts = fields.Text(compute="_compute_info_amounts")
    #info_transactions = fields.Text(compute='_compute_info_amounts')

    @api.depends('payment_method_ids', 'order_ids','cash_register_balance_start','cash_register_id')
    def _compute_info_amounts(self):
        self.get_amounts_payments()

    def get_amounts_payments(self):
        for session in self:
            payments_session = self.env['pos.payment'].search([('session_id', '=', session.id)])
            array = []
            if payments_session:
                query = """ select 
                            ppp.id as ide, ppp."name", sum(pp.amount) as total
                            from pos_payment pp inner join pos_payment_method ppp on pp.payment_method_id = ppp."id"
                            where pp.id """
                if len(payments_session.ids) > 1:
                    ids = tuple(payments_session.ids)
                    query += """  in {0} """.format(ids)
                else:
                    id = payments_session.id
                    query += """  = {0} """.format(id)
                query += """ group by ppp.id, ppp.name"""


                self.env.cr.execute(query)
                q = self.env.cr.fetchall()
                if q:
                    for res in q:
                        data_json = {
                            'ide': res[0],
                            'name': res[1],
                            'total': res[2],
                            'session_id': session.id,
                        }
                        array.append(data_json)
            session.info_amounts = json.dumps(array)
        return array

    @api.depends('payment_method_ids', 'order_ids', 'cash_register_balance_start', 'cash_register_id')
    def _compute_cash_balance_extend(self):
        for session in self:
            cash_payment_method = session.payment_method_ids.filtered('is_cash_count')[:1]
            if cash_payment_method:
                total_cash_payment = sum(self._payments_reserved(session).filtered(lambda payment: payment.payment_method_id == cash_payment_method).mapped('amount'))
                #cash_register_total_entry_encoding = session.cash_register_id.total_entry_encoding + (0.0 if session.state == 'closed' else total_cash_payment)
                amount_return = sum(session.order_ids.filtered(lambda o: not o.is_paid_total_not_efective).mapped('amount_return')) #Total de monto retornado

                session.cash_register_amount_net = total_cash_payment - amount_return
                session.cash_register_amount_returned = amount_return
            else:
                session.cash_register_amount_net = 0.0
                session.cash_register_amount_returned = 0.0

    @api.model
    def send_email_z_report(self, id):
        email_id = ''
        try:
            session_obj = self.env['pos.session'].browse(id)
            template_id = session_obj.config_id.email_template_id.id
            for user in session_obj.config_id.users_ids:
                if user.partner_id.email:
                    email_id += user.partner_id.email + ","
            template_obj = self.env['mail.template'].browse(template_id).with_context(email_to=email_id)
            report_id = self.env['ir.actions.report'].search([('report_name', '=', 'aspl_pos_close_session.pos_z_report_template')])
            if template_obj and report_id:
                template_obj.write({'report_name': 'Z Report'})
                template_obj.write({'report_template': report_id.id})
                template_obj.send_mail(session_obj.id, force_send=True)
            else:
                _logger.error('Mail Template and Report not defined!')
        except Exception as e:
            _logger.error('Unable to send email for z report of session %s', e)

    def custom_close_pos_session(self):
        for session in self:
            if session.config_id.email_close_session_report:
                self.send_email_z_report(session.id)
            if not session.config_id.cash_control:
                session.action_pos_session_closing_control()
                return True
            if session.config_id.cash_control:
                session.action_pos_session_closing_control()
                return self._validate_session()

    def cash_control_line(self, vals):
        cash_line = []
        if vals:
            cashbox_end_id = self.env['account.bank.statement.cashbox'].create([{}])
            for data in vals:
                cash_line.append((0, 0, {
                    'coin_value': data.get('coin_value'),
                    'number': data.get('number_of_coins'),
                    'subtotal': data.get('subtotal'),
                    'cashbox_id': cashbox_end_id.id,
                }))
            cashbox_end_id.write({'cashbox_lines_ids': cash_line})
        for statement in self.statement_ids:
            statement.write({'cashbox_end_id': cashbox_end_id.id, 'balance_end_real': cashbox_end_id.total})
        return True

    def set_cashbox_opening(self, opening_balance):
        self.state = 'opened'
        self.cash_register_id.balance_start = opening_balance

    def get_gross_total(self):
        gross_total = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    gross_total += line.qty * (line.price_unit - line.product_id.standard_price)
        return gross_total

    def get_product_cate_total(self):
        balance_end_real = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    balance_end_real += (line.qty * line.price_unit)
        return balance_end_real

    def get_net_gross_total(self):
        net_gross_profit = 0.0
        if self:
            net_gross_profit = self.get_gross_total() - self.get_total_tax()
        return net_gross_profit

    def get_product_name(self, category_id):
        if category_id:
            category_name = self.env['pos.category'].browse([category_id]).name
            return category_name

    def get_product_category(self):
        product_list = []
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    flag = False
                    product_dict = {}
                    for lst in product_list:
                        if line.product_id.pos_categ_id:
                            if lst.get('pos_categ_id') == line.product_id.pos_categ_id.id:
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                        else:
                            if lst.get('pos_categ_id') == '':
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                    if not flag:
                        product_dict.update({
                            'pos_categ_id': line.product_id.pos_categ_id and line.product_id.pos_categ_id.id or '',
                            'price': (line.qty * line.price_unit)
                        })
                        product_list.append(product_dict)
        return product_list

    def get_journal_amount(self):
        journal_list = []
        if self.statement_ids:
            for statement in self.statement_ids:
                journal_dict = {}
                journal_dict.update({'journal_id': statement.journal_id and statement.journal_id.name or '',
                                     'ending_bal': statement.balance_end_real or 0.0})
                journal_list.append(journal_dict)
        return journal_list

    def get_total_closing(self):
        return self.cash_register_balance_end_real

    def get_total_sales(self):
        total_price = 0.0
        if self:
            for order in self.order_ids:
                total_price += sum([(line.qty * line.price_unit) for line in order.lines])
        return total_price

    def get_total_tax(self):
        if self:
            total_tax = 0.0
            pos_order_obj = self.env['pos.order']
            total_tax += sum([order.amount_tax for order in pos_order_obj.search([('session_id', '=', self.id)])])
        return total_tax

    def get_vat_tax(self):
        taxes_info = []
        if self:
            tax_list = [tax.id for order in self.order_ids for line in
                        order.lines.filtered(lambda line: line.tax_ids_after_fiscal_position) for tax in
                        line.tax_ids_after_fiscal_position]
            tax_list = list(set(tax_list))
            for tax in self.env['account.tax'].browse(tax_list):
                total_tax = 0.00
                net_total = 0.00
                for line in self.env['pos.order.line'].search(
                        [('order_id', 'in', [order.id for order in self.order_ids])]).filtered(
                    lambda line: tax in line.tax_ids_after_fiscal_position):
                    total_tax += line.price_subtotal * tax.amount / 100
                    net_total += line.price_subtotal
                taxes_info.append({
                    'tax_name': tax.name,
                    'tax_total': total_tax,
                    'tax_per': tax.amount,
                    'net_total': net_total,
                    'gross_tax': total_tax + net_total
                })
        return taxes_info

    def get_total_discount(self):
        total_discount = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                total_discount += sum([((line.qty * line.price_unit) * line.discount) / 100 for line in order.lines])
        return total_discount

    def get_total_first(self):
        total = 0.0
        if self:
            total = (self.get_total_sales() + self.get_total_tax()) \
                    - (abs(self.get_total_discount()))
        return total

    def get_session_date(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = timezone(self._context.get('tz'))
            else:
                tz = pytz.utc
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            if sign == '+':
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) + \
                            timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) - \
                            timedelta(hours=hour_tz, minutes=min_tz)
            return date_time.strftime('%d/%m/%Y %I:%M:%S %p')

    def get_session_time(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = timezone(self._context.get('tz'))
            else:
                tz = pytz.utc
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            if sign == '+':
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) + \
                            timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) - \
                            timedelta(hours=hour_tz, minutes=min_tz)
            return date_time.strftime('%I:%M:%S %p')

    def get_current_date(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%d/%m/%Y')
        else:
            return date.today().strftime('%d/%m/%Y')

    def get_current_time(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
            c_time = datetime.now(tz)
            return c_time.strftime('%I:%M %p')
        else:
            return datetime.now().strftime('%I:%M:%S %p')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import float_is_zero

class PosPayment(models.Model):
    _inherit = "pos.payment"

    partner_id = fields.Many2one('res.partner',related="pos_order_id.partner_id", store=True)
    pos_reference = fields.Char(related="pos_order_id.pos_reference", store=True)
    date_order = fields.Datetime(related="pos_order_id.date_order", store=True)
    credit_client = fields.Boolean(string='Crédito a favor del cliente', store=True, compute='compute_credit_client')
    #credit_client = fields.Boolean(string='Crédito a favor del cliente', store=True)
    is_used = fields.Boolean(default=False, string='Usado', store=True )
    is_partial_used = fields.Boolean(default=False, string='Usado parcialmente', store=True )
    order_used = fields.Many2one('pos.order',string=u'Se usó en la orden')
    orders_used = fields.Many2many('pos.order',string=u'Órdenes usadas')
    amount_used = fields.Monetary('Monto usado', default=0.0)

    @api.depends('amount')
    def compute_credit_client(self):
        for paid in self:
            if paid.amount < 0:
                paid.credit_client = True

    @api.onchange('amount')
    def _onchange_amount(self):
        self.credit_client = False
        if self.amount < 0:
            self.credit_client = True

    # @api.model
    # def payments_credit_partner(self,partner_id):
    #     payments_array = []
    #     if partner_id:
    #         payments = self.env['pos.payment'].sudo().search([('amount','<',0),('is_used','=',False),('pos_order_id.partner_id','=',partner_id)])
    #         for p in payments:
    #             js = {
    #                 'id': p.id,
    #                 'ref': p.pos_order_id.pos_reference,
    #                 'name': p.name,
    #                 'amount': abs(p.amount),
    #                 'payment_method_id': p.payment_method_id.id,
    #                 'payment_date': p.payment_date.date(),
    #             }
    #             payments_array.append(js)
    #
    #     return payments_array



class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_refund = fields.Boolean(default=False, string=u'Usado para devolución')

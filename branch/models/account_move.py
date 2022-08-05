# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

import logging
_logger = logging.getLogger(__name__)
class AccountMove(models.Model):
    _inherit = 'account.move'

    move_comission_id = fields.Many2one('account.move', string='Asiento de comisión bancaria')
    forma_pago_id = fields.Many2one(comodel_name="pos.payment.method", string='Forma de pago', store=True)




class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    move_comission_id = fields.Many2one('account.move',string='Asiento de comisión bancaria')
    forma_pago_id = fields.Many2one(comodel_name="pos.payment.method", string='Forma de pago', store=True)
    #pos_payment_method_ids = fields.Many2many('pos.payment.method', string='Método de pago', store=True,compute="compute_payment_method_ids")

    # @api.depends('name')
    # def compute_payment_term(self):
    #     for aml in self:
    #         if aml.name:
    #             payment_method = self.env['pos.payment.method'].sudo().search([('receivable_account_id','=', aml.account_id.id)],limit=1)
    #             if payment_method:
    #                 aml.forma_pago_id = payment_method
    # @api.depends('name')
    # def compute_payment_method_ids(self):
    #     for aml in self:
    #         if aml.name:


    #
    # def init(self):
    #     amls = self.env['account.move.line'].sudo().search([('parent_state','=','posted'),('forma_pago_id','=',False)])
    #     if amls:
    #         for aml in amls:
    #             # if aml.account_id.id in [7,163,164,165,166,167,168,169]:
    #             #     a=1
    #             payment_method = self.env['pos.payment.method'].sudo().search([('receivable_account_id', '=', aml.account_id.id)], limit=1)
    #             if payment_method:
    #                 aml.forma_pago_id = payment_method
    #





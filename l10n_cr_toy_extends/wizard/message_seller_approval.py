# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class MessageSellerApprovalWizard(models.TransientModel):
    _name = 'message.seller.approval.wizard'
    _description = 'Aprobación de vendedor'

    sale_id = fields.Many2one('sale.order')


    def confirm_sale(self):
        self.sale_id.type_confirm = 'odoo'
        self.sale_id.confirmation_seller = False
        self.sale_id.sudo().action_confirm()



    def confirm_sale_with_seller_confirmation(self):
        self.sale_id.type_confirm = 'seller'
        self.sale_id.confirmation_seller = True
        self.sale_id.sudo().action_confirm()

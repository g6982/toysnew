
from odoo import api, fields, models, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
class ResPartnerIn(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'


    def get_pos_payment_by_client(self):
        payment_last = self.env['pos.payment'].sudo().search([('partner_id','=',self.id),
                                                          ('is_used','=',False),
                                                          ('credit_client','=',True)
                                                          ], limit=1)
        result = {}
        if payment_last:
            return {
                'amount': payment_last.amount,
                'amount_used': payment_last.amount_used,
                'credit_client': payment_last.credit_client,
                'date_order': payment_last.pos_order_id.date_order,
                'id': payment_last.id,
                'is_used': payment_last.is_used,
                'journal_id': [payment_last.payment_method_id.id,payment_last.payment_method_id.name],
                'partner_id': [payment_last.partner_id.id,payment_last.partner_id.name],
                'pos_reference': payment_last.pos_order_id.pos_reference
            }
        return result

from odoo import api, fields, models, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
class ResPartnerIn(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'


    discount_partner = fields.Float(string='Descuento', default=0.0)

    dob = fields.Date(string='Fecha nacimiento')
    age = fields.Integer(compute='_cal_age', store=True, readonly=True)

    @api.depends('dob')
    def _cal_age(self):
        for record in self:
            if record.dob:
                years = relativedelta(date.today(), record.dob).years
                record.age = str(int(years))
            else:
                record.age = 0



    # def get_pos_payment_by_client(self):
    #     payments = self.env['pos.payment'].sudo().search([('partner_id','=',self.id),
    #                                                       ('is_used','=',False),
    #                                                       ('credit_client','=',True)
    #                                                       ])
    #     result = []
    #     if payments:
    #         for p in payments:
    #             if (abs(p.amount) - p.amount_used) > 0:
    #                 result.append({
    #                     'id': p.id,
    #                     'pos_reference': p.pos_order_id.pos_reference,
    #                     'date_order': p.pos_order_id.date_order,
    #                     'method_paid_id': p.payment_method_id.id,
    #                     'method_paid_name': p.payment_method_id.name,
    #                     'amount': abs(p.amount) - p.amount_used,
    #                 })
    #     return result
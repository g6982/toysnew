# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import api, fields, models, _


class WebsiteStorePickup(models.Model):
    _name = 'website.store.pickup.settings'
    _description = 'Website Store Pickup'

    is_active = fields.Boolean(string="Active on website")
    name = fields.Char(string="Name", required=True, translate=True)

    customer_lead_time = fields.Selection([('store_lead', 'Use Store Lead Time'),
                                           ('product_lead', 'Use Product Lead Time')
                                           ], string="Default Pickup Lead Time", default="store_lead")

    order_premission = fields.Selection([('all', 'All'),
                                         ('condition', 'Condition')
                                         ], string="Allow Order", default="all")

    qty_type = fields.Selection([('on_hand', 'On Hand'),
                                 ('forecasted', 'Forecasted')
                                 ], string="Quantity Type", default="on_hand")

    product_qty = fields.Float(string="Product Quantity")

    @api.model
    def create_wizard(self):
        wizard_id = self.env['website.message.wizard'].create(
            {'message': "Currently a Configuration Setting for Website Store Pickup is active. You can not active other Configuration Setting. So, If you want to deactive the previous active configuration setting and active new configuration then click on 'Deactive Previous And Active New' button else click on 'cancel'."})
        return {
            'name': _("Message"),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'website.message.wizard',
            'res_id': int(wizard_id.id),
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'
        }


    def toggle_is_active(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """

        active_ids = self.search([('is_active', '=', True), ('id', 'not in', [self.id])])
        for record in self:
            if active_ids:
                return self.create_wizard()
            record.is_active = not record.is_active

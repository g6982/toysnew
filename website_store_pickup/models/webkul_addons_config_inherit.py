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


class WebkulWebsiteAddons(models.TransientModel):
    _inherit = 'webkul.website.addons'

    ##inherit the module for adding config option in webkul_website_addons

    def get_store_pick_configuration_view(self):
        store_pickup_ids = self.env['website.store.pickup.settings'].search([])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('website_store_pickup.action_store_pick_up_settings')
        list_view_id = imd.xmlid_to_res_id('website_store_pickup.view_store_pick_up_settings_tree')
        form_view_id = imd.xmlid_to_res_id('website_store_pickup.view_store_pickup_settings')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(store_pickup_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = store_pickup_ids[0].id
        return result

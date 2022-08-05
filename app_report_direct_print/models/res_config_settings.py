# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    app_print_auto = fields.Boolean('Direct Print', help="When enable, the report would auto print to default printer.")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()

        app_print_auto = True if ir_config.get_param('app_print_auto') == "True" else False
        res.update(
            app_print_auto=app_print_auto,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        ir_config.set_param("app_print_auto", self.app_print_auto or "False")


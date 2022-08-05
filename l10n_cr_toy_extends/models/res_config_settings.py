# -*- coding: utf-8 -*-
from odoo import fields, models, api


APPROVED = [('before', 'Aprobar antes de la orden de entrega'), ('after', 'Aprobar después de la orden de entrega')]

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    confirmation_seller = fields.Boolean('Confirmación para vendedor',related='company_id.confirmation_seller',readonly=False)

    #@overrite
    due_date_check = fields.Boolean(string="Fecha vencimiento", related="company_id.due_date_check", readonly=False)
    sale_approve = fields.Selection(APPROVED, related="company_id.sale_approve", readonly=False, string=u"Aprobación")
    inventory_approve = fields.Boolean(related="company_id.inventory_approve", readonly=False, string=u"Aprobación")

    location_available_id = fields.Many2one('stock.location', string='Location available', related='company_id.location_available_id', readonly=False)

class ResCompany(models.Model):
    _inherit = "res.company"

    confirmation_seller = fields.Boolean('Confirmación para vendedor')

    # @overrite
    due_date_check = fields.Boolean(string="Due Date")
    sale_approve = fields.Selection(APPROVED, default='after', string="Sale Approve")
    inventory_approve = fields.Boolean()
    location_available_id = fields.Many2one('stock.location')


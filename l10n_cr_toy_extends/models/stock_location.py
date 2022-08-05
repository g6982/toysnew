# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductTemplate, self).create(vals_list)
        if res:
            res._onchange_route_ids()
        return res

    @api.onchange('route_ids')
    def _onchange_route_ids(self):
        for record in self:
            if record.ids:
                all_routes = record.env['stock.location.route'].sudo().search([])
                route_in = record.env['stock.location.route'].sudo().search([('id', '=', record.route_ids.ids)])
                not_routes = all_routes - route_in
                for route in route_in:
                    route.write({'product_template_ids': [(4, record.ids[0])]})

                for not_route in not_routes:
                    not_route.write({'product_template_ids': [(3, record.ids[0])]})

class Route(models.Model):
    _inherit = 'stock.location.route'

    product_template_ids = fields.Many2many('product.template', 'stock_route_product_template', 'sl_route_id', 'product_tmpl_id',
                                            string='Productos')

    product_template_count = fields.Integer(compute='_compute_product_template_count')

    def to_assign_all_products(self):
        for record in self:
            product_template_ids = record.product_template_ids
            tmpl_out_ids = record.env['product.template'].sudo().search([('route_ids','not in',[record.id])])
            tmpl_in_ids = record.env['product.template'].sudo().search([('route_ids','in',[record.id])])

            if tmpl_in_ids:
                record.product_template_ids += tmpl_in_ids

            if tmpl_out_ids:
                tmpl_out_ids.write({'route_ids': [(4, record.id)]})
                record.product_template_ids += tmpl_out_ids
                # for tmpl_id in tmpl_out_ids:
                #     tmpl_id.write({'route_ids': [(4, record.id)]})
                    #record.product_template_ids += tmpl_id

    @api.depends('product_template_ids')
    def _compute_product_template_count(self):
        for record in self:
            record.product_template_count = len(record.product_template_ids)

    def action_view_products(self):
        kanban_id = self.env.ref('product.product_template_kanban_view').id
        list_id = self.env.ref('product.product_template_tree_view').id
        form_id = self.env.ref('product.product_template_only_form_view').id
        return {
            'name': _('Productos'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'res_model': 'product.template',
            'domain': [('id', 'in', self.product_template_ids.ids)],
            'views': [[kanban_id, "kanban"], [list_id, "tree"], [form_id, "form"]]
        }

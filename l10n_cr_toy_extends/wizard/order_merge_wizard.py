# -*- coding: utf-8 -*-
from array import _array_reconstructor

from odoo.exceptions import Warning
from odoo import api,models, fields, _
from odoo.tests import Form
from odoo.exceptions import AccessError, UserError, ValidationError

TYPE = [
    ('new', 'Nuevo pedido y cancelar seleccionado'),
    ('exist_1', 'Fusionar pedido en uno existente y cancelar otros')
]

NEW_TYPE_LINES = [
    ('e','Tener en cuenta líneas iguales(producto, precio, descuento)'),
    ('d','Unir todas las líneas')
]

class OrderMergeWizard(models.TransientModel):
    _inherit = 'order.merge'

    new_type = fields.Selection(selection=TYPE, string='Merge Type', default='new',required=True)
    lines = fields.Many2many('order.merge.lines')
    new_type_lines = fields.Selection(selection=NEW_TYPE_LINES, string='Detalle', default='e', required=True)


    def _evalue_lines(self, line1, line2):
        if len(line1) == len(line2):
            sw = 0
            for l1 in line1:
                for l2 in line2:
                    if l1.product_id.id == l2.product_id.id and \
                            l1.price_unit == l2.price_unit and \
                            l1.discount == l2.discount:
                        sw = 0
                    else:
                        sw = 1
            if sw == 1:
                return False
            else:
                return True
        else:
            return False
    #
    # @api.model
    # def default_get(self, fields):
    #     rec = super(OrderMergeWizard, self).default_get(fields)
    #     context = dict(self._context or {})
    #     active_ids = context.get('active_ids')
    #
    #     if active_ids:
    #         sales = self.env['sale.order'].browse(active_ids)
    #
    #         if any(sale.state == 'done' for sale in sales):
    #             raise UserError('You can not merge done orders.')
    #
    #
    #         lines = self._evaluing_orders(sales)
    #
    #         if 'lines' in fields:
    #             rec.update({'lines': lines})
    #     return rec



    #def _lines_equals(self, line1, line2):

    def _evaluing_orders(self, sales):
        orders_all = []
        sale_order_group = []
        c = 0
        for so in sales:
            if so.state in ('draft'):
                if len(sale_order_group) == 0:
                    c += 1
                    sale_order_group.append({'group': c, 'sale_orders': so})
                else:
                    sw = 0
                    for soxs in sale_order_group:
                        sox = soxs['sale_orders']
                        # if self._evalue_lines(sox.order_line, so.order_line):
                        if self.new_type_lines in ['e', False]:
                            if so.partner_id.id == sox.partner_id.id and so.pricelist_id.id == sox.pricelist_id.id and so.user_id.id == sox.user_id.id \
                                    and self._evalue_lines(sox.order_line, so.order_line):
                                sw = 1
                                break
                        elif self.new_type_lines == 'd':
                            if so.partner_id.id == sox.partner_id.id and so.pricelist_id.id == sox.pricelist_id.id and so.user_id.id == sox.user_id.id :
                                sw = 1
                                break

                    if sw == 1:
                        soxs['sale_orders'] += so
                    else:
                        c += 1
                        sale_order_group.append({'group': c, 'sale_orders': so})

        lines = []
        if len(sale_order_group) > 0:
            for group in sale_order_group:
                lines.append((0, 0, {
                    'count': len(group['sale_orders']),
                    'sale_order': [(6, 0, group['sale_orders'].ids)],
                    'process': 'to_process' if len(group['sale_orders']) > 1 else 'no_process'
                }))

        return lines


    #
    # @api.onchange('new_type_lines', 'new_type')
    # def _onchange_new_type_lines(self):
    #
    #     self.lines.unlink()
    #     context = dict(self._context or {})
    #     active_ids = context.get('active_ids')
    #
    #     val = self.new_type_lines
    #
    #     if active_ids:
    #         sales = self.env['sale.order'].browse(active_ids)
    #
    #         if any(sale.state == 'done' for sale in sales):
    #             raise UserError('You can not merge done orders.')
    #
    #         lines = self._evaluing_orders(sales)
    #         if lines:
    #             self.update({'lines': lines})
    #
    #     #return res

    @api.onchange('new_type_lines')
    def _onchange_new_type_lines(self):
        a=1
        context = self.env.context
        active_ids = context.get('active_ids')

        if active_ids:
            sales = self.env['sale.order'].browse(active_ids)

            if any(sale.state == 'done' for sale in sales):
                raise UserError('You can not merge done orders.')

            lines = self._evaluing_orders(sales)
            if lines:
                self.write({'lines':  [(6,0,[])]})
                self.write({'lines': lines})


    def merge(self):
        sale_obj = self.env['sale.order'].sudo()
        line_obj = self.env['sale.order.line'].sudo()
        cancel_list = []

        def _referencias(sale_orders):
            customer_ref = []
            msg_origin = ""
            myString = ''
            for sale in sale_orders:
                if sale.client_order_ref:
                    customer_ref.append(sale.client_order_ref)
                    if len(customer_ref) > 1:
                        myString = ",".join(customer_ref)

                    else:
                        myString = customer_ref[0]

                if msg_origin == "":
                    msg_origin += sale.name
                else:
                    msg_origin += (", " + sale.name)

            return myString, msg_origin


        def _so_to_cancel(so_cancels):
            if so_cancels:
                for o_cancel in so_cancels:
                    o_cancel.action_cancel()

        def _create_order(sale_orders):
            partner_name = sale_orders and sale_orders[0].partner_id.id
            new_sale = sale_obj.create({'partner_id': partner_name,
                                        'pricelist_id': sale_orders[0].pricelist_id.id,
                                        'user_id': sale_orders[0].user_id.id,
                                        'warehouse_id': sale_orders[0].warehouse_id.id })
            cus_ref, msg = _referencias(sale_orders)

            #_list_to_cancel(sale_orders)

            lines_to_array = []
            sale_order_lines = sale_orders.mapped('order_line')
            for sol in sale_order_lines:
                def _new_line(array_to_line, so_line, so_new):
                    array_to_line.append({
                        'product_id': so_line.product_id.id or False,
                        'discount': so_line.discount or 0,
                        'product_uom_qty': so_line.product_uom_qty or 0,
                        'price_unit': so_line.price_unit or 0,
                        'tax_id': [(6, 0, [tax.id for tax in so_line.tax_id if so_line.tax_id])] or False,
                        'metro_cubico': so_line.metro_cubico,
                        'product_packaging': so_line.product_packaging.id if so_line.product_packaging else False,
                        'order_id': so_new.id,
                    })

                if len(lines_to_array) == 0:
                   _new_line(lines_to_array, sol, new_sale)
                else:
                    sw=0
                    for ar in lines_to_array:
                        if ar['product_id'] == sol.product_id.id and ar['price_unit'] == sol.price_unit and ar['discount'] == sol.discount:
                            sw=1
                            break
                    if sw==1:
                        ar['product_uom_qty'] += sol.product_uom_qty if sol.product_uom_qty else 0
                    else:
                        _new_line(lines_to_array, sol, new_sale)

            if len(lines_to_array) > 0:
                for nw in lines_to_array:
                    line_obj.create(nw)
                    #nw_line_to_create.append((0,0,nw))

                #if len(nw_line_to_create) > 0:
                    #line_obj.create(nw_line_to_create)

            new_sale.write({'client_order_ref': cus_ref, 'origin': msg,  'so_origin_ids': [(6, 0,sale_orders.ids)]})
            msg_body = _("Creación a partir de órdenes: <b>%s</b> ") % (msg)
            new_sale.message_post(body=msg_body)
            _so_to_cancel(sale_orders)

            return new_sale



        def _write_order(sale_orders):
            cus_ref, msg = _referencias(sale_orders)
            first_sale_order = sale_orders[0]
            orders_to_cancel = sale_orders - first_sale_order
            #_list_to_cancel(orders_to_cancel)

            sale_order_lines = orders_to_cancel.mapped('order_line')
            first_lines_so = first_sale_order.order_line

            array_lines = []
            for line1 in first_lines_so:
                for sol in sale_order_lines:
                    if sol.product_id.id == line1.product_id.id and sol.price_unit == line1.price_unit and sol.discount == line1.discount:
                        line1.write({'product_uom_qty': line1.product_uom_qty + (sol.product_uom_qty if sol.product_uom_qty else 0)})
                    else:
                        data_line = {
                            'product_id': sol.product_id.id or False,
                            'discount': sol.discount or 0,
                            'product_uom_qty': sol.product_uom_qty or 0,
                            'price_unit': sol.price_unit or 0,
                            'tax_id': [(6, 0, [tax.id for tax in sol.tax_id if sol.tax_id])] or False,
                            'metro_cubico': sol.metro_cubico,
                            'product_packaging': sol.product_packaging.id if sol.product_packaging else False,
                            'order_id': first_sale_order.id,
                        }

                        array_lines.append(data_line)

            if len(array_lines) > 0:
                self.env['sale.order.line'].sudo().create(array_lines)


            #new_sale.write({'client_order_ref': cus_ref, 'origin': msg})

            _so_to_cancel(orders_to_cancel)

            msg_body = _("Unión de órdenes: <b>%s</b> - Órden principal: %s") % (msg, first_sale_order.name)
            first_sale_order.message_post(body=msg_body)
            first_sale_order.origin = msg
            first_sale_order.write({'so_origin_ids': [(6, 0,sale_orders.ids)]})

            return first_sale_order

        orders_returns = []
        def _run_orders(lines_detail, type_o):
            for line_detail in lines_detail:
                if line_detail.sale_order and line_detail.process == 'to_process':
                    if type_o == 'new':
                        #for so in line_detail.sale_order:
                        order_return = _create_order(line_detail.sale_order)
                        orders_returns.append(order_return)
                    else:
                        #for so in line_detail.sale_order:
                        order_return = _write_order(line_detail.sale_order)
                        orders_returns.append(order_return)

            return orders_returns

        list_order_returns = False
        if self.new_type == 'new':
            list_order_returns = _run_orders(self.lines, self.new_type)

        elif self.new_type == 'exist_1':
            list_order_returns = _run_orders(self.lines, self.new_type)

        else:
            pass

        if list_order_returns:
            ids = []
            for so_with_id in list_order_returns:
                ids.append(so_with_id.id)

            result = {
                'name': _('Órdenes creadas'),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'list',
                'domain': [('id','in',ids)],
                'views': [(self.env.ref('sale.view_quotation_tree').id, 'list'),(self.env.ref('sale.view_order_form').id, 'form')]
            }
            return result




    # def re_calculate_orders(self):
    #
    #     self.lines.unlink()
    #     context = dict(self._context or {})
    #     active_ids = context.get('active_ids')
    #
    #     if active_ids:
    #         sales = self.env['sale.order'].browse(active_ids)
    #
    #         if any(sale.state == 'done' for sale in sales):
    #             raise UserError('You can not merge done orders.')
    #
    #         lines = self._evaluing_orders(sales)
    #         if lines:
    #             self.update({'lines': lines})
    #
    #
    #         r = {
    #             "type": "ir.actions.act_window",
    #             "view_type": "form",
    #             "view_mode": "form",
    #             "res_id": self.id,
    #             "res_model": "order.merge",
    #             "context": {
    #                 'default_new_type': self.new_type,
    #                 'default_new_type_lines': self.new_type_lines,
    #             },
    #             "target": "new",
    #         }
    #
    #         return r

class OrderMergeLines(models.TransientModel):
    _name = 'order.merge.lines'

    count = fields.Integer(string='Cantidad')
    sale_order = fields.Many2many('sale.order', string='Órdenes')
    process = fields.Selection(selection=[('to_process','A procesar'), ('no_process','No procesa')], string='Estado')
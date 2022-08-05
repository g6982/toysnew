# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

TYPE = [
    ('new', 'Nuevo picking y cancelar seleccionado'),
    ('exist_1', 'Fusionar picking en uno existente y cancelar otros')
]

NEW_TYPE_LINES = [
    ('e','Tener en cuenta líneas iguales(producto, precio, descuento)'),
    ('d','Unir todas las líneas')
]

class PickingMergeWizard(models.TransientModel):
    _name = 'picking.merge.wizard'
    _description = 'Unir picking'

    new_type = fields.Selection(selection=TYPE, string=u'Tipo unión', default='new', required=True)
    lines = fields.Many2many('picking.merge.lines')
    new_type_lines = fields.Selection(selection=NEW_TYPE_LINES, string='Detalle', default='e', required=True)


    def _evalue_lines(self, line1, line2, type):
        if len(line1) == len(line2):
            sw = 0
            for l1 in line1:
                for l2 in line2:
                    if type=='sale':
                        if l1.product_id.id == l2.product_id.id and \
                                l1.price_unit == l2.price_unit and \
                                l1.discount == l2.discount:
                            sw = 0
                        else:
                            sw = 1
                    elif type=='purchase':
                        if l1.product_id.id == l2.product_id.id and \
                                l1.price_unit == l2.price_unit:
                            sw = 0
                        else:
                            sw = 1

            if sw == 1:
                return False
            else:
                return True
        else:
            return False


    def _evaluing_picking(self, pickings):
        picking_group = []
        count = 0


        def _filtered_picking_header(picking, spx):
            bnd = 0
            sp_r = False
            for sp in spx['picking_ids']:
                if picking.location_id.id == sp.location_id.id and picking.location_dest_id.id == sp.location_dest_id.id and picking.branch_id.id == sp.branch_id.id\
                        and picking.picking_type_id.id == sp.picking_type_id.id and picking.state == sp.state:
                    bnd = 1
                    sp_r = sp
                    break

            return bnd, sp_r


        def _filtered_sales(picking, spx, spxs, c):
            good_sale = 0
            sw=0
            sale_id = picking.sale_id
            for sp in spx: #spx = stock picking de array
                sale_x_id = sp.sale_id
                if sp.id != picking.id and sp.picking_type_id.id == picking.picking_type_id.id and picking.state == sp.state:
                    if sale_id and sale_x_id:
                        good_sale = 1
                        if self.new_type_lines in ['e', False]:
                            if sale_id.partner_id.id == sale_x_id.partner_id.id and sale_id.pricelist_id.id == sale_x_id.pricelist_id.id \
                                    and sale_id.user_id.id == sale_x_id.user_id.id \
                                    and self._evalue_lines(sale_id.order_line, sale_x_id.order_line, 'sale'):
                                sw = 1
                                break

                        elif self.new_type_lines == 'd':
                            if sale_id.partner_id.id == sale_x_id.partner_id.id and sale_id.pricelist_id.id == sale_x_id.pricelist_id.id \
                                    and sale_id.user_id.id == sale_x_id.user_id.id:
                                sw = 1
                                break


            if sw == 1:
                rsp, sp_r = _filtered_picking_header(picking, spxs) #response stock picking
                if rsp == 1 and sp_r:
                    spxs['picking_ids'] += picking
                else:
                    picking_group.append({'group': c, 'picking_ids': picking})

            # elif sale_id:
            #     good_sale = 1
            #     picking_group.append({'group': c, 'picking_ids': picking})

            return sw

        def _filtered_puchase(picking, spx, spxs, c):
            good_purchase = 0
            sw = 0
            purchase_id = picking.purchase_id
            for sp in spx: #spx = stock picking de array
                purchase_x_id = sp.purchase_id
                if sp.id != picking.id and sp.picking_type_id.id == picking.picking_type_id.id and picking.state == sp.state:
                    if purchase_id and purchase_x_id:
                        good_purchase = 1
                        if self.new_type_lines in ['e', False]:
                            if purchase_id.partner_id.id == purchase_x_id.partner_id.id and purchase_id.pricelist_id.id == purchase_x_id.pricelist_id.id \
                                    and purchase_id.user_id.id == purchase_x_id.user_id.id \
                                    and self._evalue_lines(purchase_id.order_line, purchase_x_id.order_line, 'purchase'):
                                sw = 1
                                break

                        elif self.new_type_lines == 'd':
                            if purchase_id.partner_id.id == purchase_x_id.partner_id.id and purchase_id.pricelist_id.id == purchase_x_id.pricelist_id.id \
                                    and purchase_id.user_id.id == purchase_x_id.user_id.id:
                                sw = 1
                                break

            if sw == 1:
                rsp, sp_r = _filtered_picking_header(picking, spxs)  # response stock picking
                if rsp == 1 and sp_r:
                    spxs['picking_ids'] += picking
                else:
                    picking_group.append({'group': c, 'picking_ids': picking})
            #
            # elif purchase_id:
            #     good_purchase = 1
            #     picking_group.append({'group': c, 'picking_ids': picking})

            return sw

        for picking in pickings:
            _logger.info(picking.name)
            #if picking.name == 'URUCA/PICK/00004 ':
            #    a=1
            sale_id = picking.sale_id
            purchase_id = picking.purchase_id
            if len(picking_group) == 0:
                count += 1
                picking_group.append({'group': count, 'picking_ids': picking, 'picking_type': picking.picking_type_id, 'state': picking.state})
            else:
                x_rsp = 0
                if sale_id or purchase_id:
                    r_sale=0
                    r_purchase=0
                    if sale_id:
                        for spxs in picking_group:
                            spx = spxs['picking_ids']
                            r_sale = _filtered_sales(picking, spx, spxs, count)
                            if r_sale==1:
                                break

                        if r_sale==0:
                            picking_group.append({'group': count, 'picking_ids': picking})
                    elif purchase_id:
                        for spxs in picking_group:
                            spx = spxs['picking_ids']
                            r_purchase = _filtered_puchase(picking, spx, spxs, count)
                            if r_sale == 1:
                                break

                        if r_purchase == 0:
                            picking_group.append({'group': count, 'picking_ids': picking})


                        # if not r_sale:
                        #     r_purchase = _filtered_puchase(picking, spx, spxs, count)
                        #     if r_purchase:
                        #         break
                        # else:
                        #     break

                else:
                    sp = False
                    for spxs in picking_group:
                        x_rsp, sp = _filtered_picking_header(picking, spxs)  # response stock picking
                        if x_rsp == 1:
                            break

                    if x_rsp == 1 and sp:
                        sp['picking_ids'] += picking

                    else:
                        picking_group.append({'group': count, 'picking_ids': picking})

        lines = []
        if len(picking_group) > 0:
            for group in picking_group:
                lines.append((0, 0, {
                    'count': len(group['picking_ids']),
                    'picking_ids': [(6, 0, group['picking_ids'].ids)],
                    'picking_type_id': group['picking_ids'][0].picking_type_id.id,
                    'state': group['picking_ids'][0].state,
                    'process': 'to_process' if len(group['picking_ids']) > 1 else 'no_process'
                }))

        return lines


    @api.onchange('new_type_lines')
    def _onchange_new_type_lines(self):

        context = self.env.context
        active_ids = context.get('active_ids')

        if active_ids:
            picking = self.env['stock.picking'].browse(active_ids).filtered(lambda sp: sp.state not in ['done', 'cancel'])

            lines = self._evaluing_picking(picking)

            #lines = self._group_picking(picking_group)

            if lines:
                self.write({'lines':  [(6,0,[])]})
                self.write({'lines': lines})

    def merge_picking(self):

        def _ordered_move_lines(move_lines_mapped):

            def _equals_lines(move, line):
                sw = 0
                if line['product_id'] == move.product_id.id and line['location_id'] == move.location_id.id \
                        and line['location_dest_id'] == move.location_dest_id.id:
                    sw = 1

                return sw

            lines = []
            for move in move_lines_mapped:
                if len(lines) == 0:
                    lines.append({
                        'name': move.name,
                        'product_id': move.product_id.id,
                        'product_uom_qty': move.product_uom_qty,
                        'product_uom': move.product_uom.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        #'package_id': move.package_id.id,
                        #'result_package_id': move.result_package_id.id,
                    })
                else:
                    r = 0
                    for l in lines:
                        r = _equals_lines(move, l)
                        if r == 1:
                            break

                    if r == 1:
                        l['product_uom_qty'] += move.product_uom_qty

                    else:
                        lines.append({
                            'name': move.name,
                            'product_id': move.product_id.id,
                            'product_uom_qty': move.product_uom_qty,
                            'product_uom': move.product_uom.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            #'package_id': move.package_id.id,
                            #'result_package_id': move.result_package_id.id,
                        })

            move_lines = []
            if len(lines) > 0:
                for line in lines:
                    move_lines.append((0,0,line))

            return move_lines



        def _create_stock_picking(self):
            pickings_created = []
            for line in self.lines:
                if line.process == 'to_process': #Solo aquellas que pueden ser procesadas
                    picking_ids = line.picking_ids
                    picking_id = picking_ids[0]

                    move_lines_mapped = picking_ids.mapped('move_lines')
                    move_lines = _ordered_move_lines(move_lines_mapped)
                    if len(move_lines) > 0:
                        pick = self.env['stock.picking'].sudo().create({
                            'location_id': picking_id.location_id.id,
                            'location_dest_id': picking_id.location_dest_id.id,
                            'partner_id': picking_id.partner_id.id,
                            'picking_type_id': picking_id.picking_type_id.id,
                            'branch_id': picking_id.branch_id.id,
                            'move_type': picking_id.move_type, #Política de entrega,
                            'move_lines': move_lines,
                            'picking_origin_ids': picking_ids.ids
                        })
                        if pick:
                            pickings_created.append(pick.id)
                            msg_origin = ""
                            for p in picking_ids:
                                if msg_origin == "":
                                    msg_origin += pick.name
                                else:
                                    msg_origin += (", " + pick.name)

                                p.sudo().action_cancel() #Cancelar los pickings relacionados

                            pick.sudo().write({'origin': msg_origin})

            return pickings_created

        def _write_stock_picking(self):
            pickings_writed = []
            for line in self.lines:
                if line.process == 'to_process':  # Solo aquellas que pueden ser procesadas
                    picking_ids = line.picking_ids
                    picking_first_id = picking_ids[0]
                    others = picking_ids - picking_first_id

                    move_lines_mapped = others.mapped('move_lines')
                    #move_lines = _ordered_move_lines(move_lines_mapped)

                    stock_move_array = []



                    for move_to_create in move_lines_mapped:
                        sw = 0
                        for move in picking_first_id.move_lines:
                            if move.product_id.id == move_to_create.product_id.id and move.location_id.id == move_to_create.location_id.id \
                                    and move.location_dest_id.id == move_to_create.location_dest_id.id:
                                move.write({'product_uom_qty': move.product_uom_qty + move_to_create.product_uom_qty})
                                sw=1


                        if sw == 0:
                            stock_move_array.append({
                                'name': move_to_create.name,
                                'product_id': move_to_create.product_id.id,
                                'product_uom_qty': move_to_create.product_uom_qty,
                                'product_uom': move_to_create.product_uom.id,
                                'location_id': move_to_create.location_id.id,
                                'location_dest_id': move_to_create.location_dest_id.id,
                                #'package_id': move_to_create.package_id.id,
                                #'result_package_id': move_to_create.result_package_id.id,
                                'picking_id': picking_first_id.id,
                            })


                    if len(stock_move_array) > 0:
                        self.env['stock.move'].sudo().create(stock_move_array)

                    msg_origin = ""

                    for pick in others:
                        if msg_origin == "":
                            msg_origin += pick.name
                        else:
                            msg_origin += (", " + pick.name)
                        pick.sudo().action_cancel() #Cancelar los pickings relacionados

                    pickings_writed.append(picking_first_id.id)
                    origin_first = picking_first_id.origin
                    if origin_first:
                        origin = origin_first + ' / ' + msg_origin
                    picking_first_id.write({'picking_origin_ids': [(6, 0,others.ids)], 'origin': origin})

            return pickings_writed

        array_ids = False
        if self.new_type == 'new':
            array_ids = _create_stock_picking(self)
        else:
            array_ids = _write_stock_picking(self)

        if array_ids :
            result = {
                'name': _('Picking creados'),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'list',
                'domain': [('id', 'in', array_ids)],
                'views': [(self.env.ref('stock.vpicktree').id, 'list'), (self.env.ref('stock.view_picking_form').id, 'form')]
            }
            return result



class PickingMergeLines(models.TransientModel):
    _name = 'picking.merge.lines'
    _description = 'Lineas para unión de picking'

    count = fields.Integer(string='Cantidad')
    picking_ids = fields.Many2many('stock.picking', string='Transferencias')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('waiting', 'Esperando otra operación'),
        ('confirmed', 'Esperando'),
        ('assigned', 'Preparado'),
        ('done', 'Realizado'),
        ('cancel', 'Cancelada'),
    ], string='Estado')
    picking_type_id = fields.Many2one('stock.picking.type', string='Tipo')
    process = fields.Selection(selection=[('to_process','A procesar'), ('no_process','No procesa')], string=u'Transacción')
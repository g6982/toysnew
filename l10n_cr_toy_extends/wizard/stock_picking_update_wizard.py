# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import api,models, fields, _
from odoo.tests import Form
from odoo.exceptions import AccessError, UserError, ValidationError

ACTION_PARTIAL = [('yes','Realizar la entrega parcial (Creará otro picking con las entregas faltantes)'),
                  ('no','No hacer entrega parcial (Cierra el picking y queda en estado "realizado")'),
                  ('cancel','Cancelar la entrega parcial (El usuario verificará el picking y lo validará de forma manual, solo actualiza las cantidad realizadas)')]

class StockPickingUpdateWizard(models.TransientModel):
    _name = 'stock.picking.update.wizard'
    _description = 'Importacion para actualización de entregas en picking'


    picking_id = fields.Many2one('stock.picking',string='Picking')
    picking_name = fields.Char(related='picking_id.name')
    categ_defult_ids = fields.Many2many(
        comodel_name='product.category',
        relation='product_category_backorder_default_rel',
        column1='backorder_id',
        column2='category_id')

    categ_ids = fields.Many2many( comodel_name='product.category',
        relation='product_category_backorder_select_rel',
        column1='backorder_id',
        column2='category_id',
        string='Categorías', required=True)

    location_default_ids = fields.Many2many(
        comodel_name='stock.location',
        relation='stock_location_backorder_default_rel',
        column1='backorder_id',
        column2='location_id')
    location_ids = fields.Many2many(
        comodel_name='stock.location',
        relation='stock_location_backorder_select_rel',
        column1='backorder_id',
        column2='location_id',
        string='Ubicaciones')

    total_lines = fields.Integer(default=0,string='Total líneas')
    check_segment = fields.Boolean(tring='Desea segmentar ? ')
    total_segment = fields.Integer(default=0,string='N° de segmentos')
    total_lots = fields.Integer(default=0,string='N° de segmentos',store=True)

    lines_ids = fields.Many2many('stock.move.line')
    action_partial = fields.Selection(ACTION_PARTIAL, default='cancel', string='La transferencia se realizará')

    mensaje = fields.Char()

    def apply_filter_backorder(self):

        lines = self.picking_id.move_line_ids_without_package

        lines_ids = lines.filtered(lambda l:l.location_id.id in self.location_ids.ids and l.product_id.categ_id.id in self.categ_ids.ids)

        context = dict(self.env.context)
        self.lines_ids = lines_ids
        self.total_lines = len(lines_ids.ids)

        return {
            u'name': u'Backorder',
            u'type': u'ir.actions.act_window',
            u'view_mode': u'form',
            u'target': u'new',
            u'res_model': u'stock.picking.update.wizard',
            u'context': context,
            u'res_id': self.id
        }

    @api.onchange('check_segment')
    def _onchange_check_segment(self):
        if not self.check_segment:
            self.total_segment = 0
            self.action_partial = 'cancel'
        else:
            self.action_partial = 'yes'

    @api.onchange('action_partial')
    def _onchange_action_partial(self):
        if self.action_partial in ('no','cancel'):
            self.total_segment = 0

        self.mensaje = False
        if self.action_partial == 'yes' and not self.total_segment:
            self.mensaje = 'Para aplicar entregas parciales debe activar la segmentación y colocar el número de registros! '
            # raise UserError(
            #     _('Para aplicar entregas parciales debe activar la segmentación y colocar el número de registros! '))
        elif self.action_partial == 'yes' and not self.total_lots > 0:
            self.mensaje = 'Para aplicar entregas parciales debe colocar el número de registros! '

        elif self.action_partial in ('no','cancel') and (self.total_segment or self.total_lots > 0):
            self.mensaje = 'No aplicará la segmentación y el número de registros ! '


    @api.onchange('total_segment')
    def _onchange_total_segment(self):
        if self.total_segment > 0 and self.total_lines < self.total_segment:
            raise UserError(
                _('La cantidad de registros por lote no debe ser mayor a la cantidad de líneas en el detalle! '))
        if self.total_segment < 0:
            raise UserError(
                _('La cantidad de registros por lote no puede ser menor a CERO.'))


        if self.total_lines > 0 and self.total_segment > 0:
            part = self._part_lots(self.total_lines, self.total_segment)
            self.total_lots = part
        else:
            self.total_lots = 0

        if self.check_segment and self.total_segment > 0:
            self.action_partial = 'yes'
            self.mensaje = False


    def create_backorders(self):
        if self.check_segment and self.total_segment > 0 and self.total_lots > 0:
            self.action_partial = 'yes'

        initial = 0
        end = self.total_segment
        picking = self.picking_id
        part = self._part_lots(self.total_lines, self.total_segment)
        self.total_lots = part
        for i in range(0, self.total_lots):

            picking = self._backorder_creation(self.lines_ids[initial:end],picking)
            initial = initial + self.total_segment
            end = end + self.total_segment


    def _backorder_creation(self,lines,picking):
        if picking:
            if self.action_partial!='yes':
                lines = self.lines_ids

            for line in lines:
                picking.move_line_ids_without_package.filtered(lambda x: x.id == line.id).write(
                    {'qty_done': line.product_uom_qty})

            res = picking.button_validate()
            if type(res) == bool:
                pass
            elif 'res_model' in res:
                wizard = Form(self.env[res['res_model']].with_context(res['context'])).save()
                if self.action_partial == 'no':
                    wizard.process_cancel_backorder()
                elif self.action_partial == 'yes':
                    wizard.process()
                else:
                    pass

            return picking.backorder_ids
        else:
            return False

    def _part_lots(self,total, lots):
        if lots==0:
            return 1
        else:
            div = total / lots
            part = int(div) + 1 if div > int(div) else int(div)

            return part

import base64
import io
from . import styles

def _body_data(self, xls, workbook):

    header_name, head, header_detalle, body_title, body, name, number =  styles._get_styles(workbook)

    company_id = self.order_id.company_id

    address = company_id.district_id.name + ', \n ' + company_id.state_id.name + ', \n ' + company_id.country_id.name


    sheet = workbook.add_worksheet(u'PURCHASE ORDER')


    #WIDTH COLUMNS
    sheet.set_column('A:A', 5)
    sheet.set_column('B:B', 10)
    sheet.set_column('C:C', 35)
    sheet.set_column('D:D', 11)
    sheet.set_column('E:E', 10)
    sheet.set_column('F:F', 11)
    sheet.set_column('G:G', 10)
    sheet.set_column('H:H', 11)
    sheet.set_column('I:I', 11)
    sheet.set_column('J:J', 12)
    sheet.set_column('K:K', 12)
    sheet.set_column('L:L', 17)

    img_data = base64.b64decode(self.order_id.company_id.logo)
    image = io.BytesIO(img_data)

    sheet.insert_image('D1', 'logo.png', {'image_data': image, 'x_scale': 1.2, 'y_scale': 1.4})


    sheet.merge_range('B1:L1', company_id.name, header_name)
    sheet.merge_range('B2:L2', ('ADD. : {0}'.format(address)), head)
    sheet.merge_range('B3:L3', ('TEL. : {0}'.format(company_id.phone or '-')), head)
    sheet.merge_range('B4:L4', ('EMAIL : {0}'.format(company_id.email or '-')), head)

    #sub titulo
    sheet.merge_range('B6:L6', 'PROFORMA INVOICE', header_detalle)

    #Cabecera detalle
    sheet.write('B8:B8', 'Buy to :', name)
    sheet.write('B9:B9', 'Address :', name)
    sheet.write('B10:B10', 'Contact :', name)

    sheet.merge_range('C8:F8', self.order_id.partner_id.name , body_title)
    sheet.merge_range('C9:F9', self.order_id.partner_id.state_id.name + ',' + self.order_id.partner_id.country_id.name , body_title)

    contacts = '-'
    if self.order_id.partner_id.child_ids:
        for c in self.order_id.partner_id.child_ids:
            if contacts == '-':
                contacts = c.name
            else:
                contacts = contacts + ',' + c.name
    sheet.merge_range('C10:F10', contacts, body_title)

    sheet.merge_range('H8:I8', 'Proforma invoice date :', name)
    sheet.merge_range('H9:I9', 'Proforma invoice number :', name)
    sheet.merge_range('H10:I10', 'Order number :', name)

    sheet.merge_range('J8:L8', self.order_id.date_approve or '-', body_title)
    sheet.merge_range('J9:L9', self.order_id.name or '-', body_title)
    sheet.merge_range('J10:L10', self.order_id.shipping_mark or '-', body_title)

    sheet.write('B12:B12', 'Sku #', name)
    sheet.write('C12:C12', 'Description', name)
    sheet.write('D12:D12', 'Barcode', name)
    sheet.write('E12:E12', 'Quantity', name)
    sheet.write('F12:F12', 'PC per carton', name)
    sheet.write('G12:G12', 'Cartons', name)
    sheet.write('H12:H12', 'CBM', name)
    sheet.write('I12:I12', 'CBM Total', name)
    sheet.write('J12:J12', 'Unit price last', name)
    sheet.write('K12:K12', 'Unit price', name)
    sheet.write('L12:L12', 'Net amount', name)

    row_pos = 11
    t_qty = 0.0
    t_number_cartons = 0.0
    t_cbm_total = 0.0
    t_net_amount = 0.0
    for line in self.order_id.order_line:
        row_pos += 1
        sheet.write(row_pos, 1, line.product_id.default_code, body)
        sheet.write(row_pos, 2, line.name, body)
        sheet.write(row_pos, 3, line.product_id.barcode or '-', body)
        sheet.write(row_pos, 4, line.product_qty, number)
        sheet.write(row_pos, 5, line.package_qty, number)
        sheet.write(row_pos, 6, line.package_qty_in, number)
        sheet.write(row_pos, 7, line.product_id.volume, number)
        sheet.write(row_pos, 8, round(line.product_id.volume * line.package_qty_in,3), number)
        sheet.write(row_pos, 9, line.price_last, number)
        sheet.write(row_pos, 10, line.price_unit, number)
        sheet.write(row_pos, 11, round(line.price_unit * line.product_qty,2), number)

        #totals
        t_qty += line.product_qty
        t_number_cartons += line.package_qty_in
        t_cbm_total += round(line.product_id.volume * line.package_qty_in,3)
        t_net_amount += round(line.price_unit * line.product_qty,2)

    row_pos += 2
    # sheet.set_row(row_pos, 12, {'bold': True})
    sheet.merge_range('B{0}:D{0}'.format(row_pos), 'TOTAL', header_detalle)
    sheet.write('E{0}:E{0}'.format(row_pos), t_qty, number)
    sheet.write('G{0}:G{0}'.format(row_pos), t_number_cartons, number)
    sheet.write('I{0}:I{0}'.format(row_pos), t_cbm_total, number)
    sheet.write('L{0}:L{0}'.format(row_pos), t_net_amount, number)









import base64
import io
from . import styles

def _body_data(self, xls, workbook):

    header_name, head, header_detalle, body_title, body, name, number =  styles._get_styles(workbook)

    company_id = self.order_id.company_id

    address = (company_id.district_id.name or '-' ) + ', \n ' + (company_id.state_id.name or '-' )+ ', \n ' + (company_id.country_id.name or '-' )


    sheet = workbook.add_worksheet(u'PURCHASE ORDER')


    #WIDTH COLUMNS
    sheet.set_column('A:A', 5)
    sheet.set_column('B:B', 10)
    sheet.set_column('C:C', 35)
    sheet.set_column('D:D', 11)
    sheet.set_column('E:E', 10)
    sheet.set_column('F:F', 11)
    sheet.set_column('G:G', 10)
    sheet.set_column('H:H', 11)
    sheet.set_column('I:I', 11)
    sheet.set_column('J:J', 12)
    sheet.set_column('K:K', 12)
    sheet.set_column('L:L', 17)

    img_data = base64.b64decode(self.order_id.company_id.logo)
    image = io.BytesIO(img_data)

    sheet.insert_image('D1', 'logo.png', {'image_data': image, 'x_scale': 1.2, 'y_scale': 1.4})


    sheet.merge_range('B1:L1', company_id.name, header_name)
    sheet.merge_range('B2:L2', ('ADD. : {0}'.format(address)), head)
    sheet.merge_range('B3:L3', ('TEL. : {0}'.format(company_id.phone or '-')), head)
    sheet.merge_range('B4:L4', ('EMAIL : {0}'.format(company_id.email or '-')), head)

    #sub titulo
    sheet.merge_range('B6:L6', 'PROFORMA INVOICE', header_detalle)

    #Cabecera detalle
    sheet.write('B8:B8', 'Buy to :', name)
    sheet.write('B9:B9', 'Address :', name)
    sheet.write('B10:B10', 'Contact :', name)

    sheet.merge_range('C8:F8', self.order_id.partner_id.name , body_title)
    sheet.merge_range('C9:F9', (self.order_id.partner_id.state_id.name or '-' ) + ',' + (self.order_id.partner_id.country_id.name or '-' ), body_title)

    contacts = '-'
    if self.order_id.partner_id.child_ids:
        for c in self.order_id.partner_id.child_ids:
            if contacts == '-':
                contacts = c.name
            else:
                contacts = contacts + ',' + c.name
    sheet.merge_range('C10:F10', contacts, body_title)

    sheet.merge_range('H8:I8', 'Proforma invoice date :', name)
    sheet.merge_range('H9:I9', 'Proforma invoice number :', name)
    sheet.merge_range('H10:I10', 'Order number :', name)

    sheet.merge_range('J8:L8', self.order_id.date_approve or '-', body_title)
    sheet.merge_range('J9:L9', self.order_id.name or '-', body_title)
    sheet.merge_range('J10:L10', self.order_id.shipping_mark or '-', body_title)

    sheet.write('B12:B12', 'Sku #', name)
    sheet.write('C12:C12', 'Description', name)
    sheet.write('D12:D12', 'Barcode', name)
    sheet.write('E12:E12', 'Quantity', name)
    sheet.write('F12:F12', 'PC per carton', name)
    sheet.write('G12:G12', 'Cartons', name)
    sheet.write('H12:H12', 'CBM', name)
    sheet.write('I12:I12', 'CBM Total', name)
    sheet.write('J12:J12', 'Unit price last', name)
    sheet.write('K12:K12', 'Unit price', name)
    sheet.write('L12:L12', 'Net amount', name)

    row_pos = 11
    t_qty = 0.0
    t_number_cartons = 0.0
    t_cbm_total = 0.0
    t_net_amount = 0.0
    for line in self.order_id.order_line:
        row_pos += 1
        sheet.write(row_pos, 1, line.product_id.default_code, body)
        sheet.write(row_pos, 2, line.name, body)
        sheet.write(row_pos, 3, line.product_id.barcode or '-', body)
        sheet.write(row_pos, 4, line.product_qty, number)
        sheet.write(row_pos, 5, line.package_qty, number)
        sheet.write(row_pos, 6, line.package_qty_in, number)
        sheet.write(row_pos, 7, line.product_id.volume, number)
        sheet.write(row_pos, 8, round(line.product_id.volume * line.package_qty_in,3), number)
        sheet.write(row_pos, 9, line.price_last, number)
        sheet.write(row_pos, 10, line.price_unit, number)
        sheet.write(row_pos, 11, round(line.price_unit * line.product_qty,2), number)

        #totals
        t_qty += line.product_qty
        t_number_cartons += line.package_qty_in
        t_cbm_total += round(line.product_id.volume * line.package_qty_in,3)
        t_net_amount += round(line.price_unit * line.product_qty,2)

    row_pos += 2
    # sheet.set_row(row_pos, 12, {'bold': True})
    sheet.merge_range('B{0}:D{0}'.format(row_pos), 'TOTAL', header_detalle)
    sheet.write('E{0}:E{0}'.format(row_pos), t_qty, number)
    sheet.write('G{0}:G{0}'.format(row_pos), t_number_cartons, number)
    sheet.write('I{0}:I{0}'.format(row_pos), t_cbm_total, number)
    sheet.write('L{0}:L{0}'.format(row_pos), t_net_amount, number)










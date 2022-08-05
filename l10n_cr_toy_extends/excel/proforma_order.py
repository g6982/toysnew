import base64
import io
from . import styles

def _body_data(self, xls, workbook):

    header_name, head, header_detalle, body_title, body, name, number =  styles._get_styles(workbook)

    company_id = self.order_id.company_id

    address = (company_id.district_id.name or '-' ) + ', \n ' + (company_id.state_id.name or '-' )+ ', \n ' + (company_id.country_id.name or '-' )


    sheet = workbook.add_worksheet(u'REQUEST FOR QUOTATION')


    #WIDTH COLUMNS
    sheet.set_column('A:A', 5)
    sheet.set_column('B:B', 17)
    sheet.set_column('C:C', 43)
    sheet.set_column('D:D', 11)
    sheet.set_column('E:E', 20)

    img_data = base64.b64decode(self.order_id.company_id.logo)
    image = io.BytesIO(img_data)

    sheet.insert_image('C1', 'logo.png', {'image_data': image, 'x_scale': 1.2, 'y_scale': 1.4})


    sheet.merge_range('B1:E1', company_id.name, header_name)
    sheet.merge_range('B2:E2', ('ADD. : {0}'.format(address)), head)
    sheet.merge_range('B3:E3', ('TEL. : {0}'.format(company_id.phone or '-')), head)
    sheet.merge_range('B4:E4', ('EMAIL : {0}'.format(company_id.email or '-')), head)

    #sub titulo
    sheet.merge_range('B6:E6', 'REQUEST FOR QUOTATION', header_detalle)

    #Cabecera detalle
    sheet.merge_range('B8:B9', 'Shipping address  :', name)

    sheet.write('C8:C8', self.order_id.picking_type_id.warehouse_id.name, body_title)
    sheet.write('C9:C9', (self.order_id.dest_address_id.state_id.name or '-' ) + ',' + (self.order_id.dest_address_id.country_id.name or '-'), body_title)

    sheet.merge_range('D8:D9', 'Partner :', name)

    sheet.write('E8:E8', self.order_id.partner_id.name or '-', body_title)
    sheet.write('E9:E9', (self.order_id.partner_id.state_id.name or '-' ) + ',' + (self.order_id.partner_id.country_id.name or '-' ), body_title)

    sheet.merge_range('B12:C12', 'Description', name)
    sheet.write('D12:D12', 'Expected Date', name)
    sheet.write('E12:E12', 'Qty', name)

    row_pos = 11

    for line in self.order_id.order_line:
        row_pos += 1
        sheet.merge_range('B{0}:C{0}'.format(row_pos + 1), line.name, body)
        sheet.write(row_pos, 3, line.date_planned, number)
        sheet.write(row_pos, 4, line.product_qty, number)









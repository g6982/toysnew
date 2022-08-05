# -*- coding: utf-8 -*-
{
    'name': "Toys-Extendido",

    'summary': """
        Requerimientos adicionales.""",

    'description': """
        1. Cálculo de m3 para compra y venta.
        2. Restricción de m3 y unidades para pedidos de compra y venta.
        3. Captura de datos par relación factura=>orden de compra.
        4. Informe de gastos.
        5. Actualización de órdenes de venta.
        6. Unión para órdenes y picking.
    """,
    'author': "XALACHI",
    'website': "https://www.xalachi.com/",
    # Categories can be used to filter modules in modules listing
    'category': 'all',
    'version': '14.0.4.4',
    # any module necessary for this one to work correctly
    'depends': ['base','sale','point_of_sale','sale_stock','purchase','purchase_product_matrix','l10n_cr_electronic_invoice','stock_move_invoice','stock','product',
                'order_merge','stock_move_invoice','pos_orders_all','customer_credit_limit_app','ywt_internal_stock_transfer','website_sale',
                'pos_order_return','pos_orders','l10n_cr_pos','pos_reserve_order_app','aspl_pos_close_session'],
    # always loaded
    'data': [
        'security/groups_customers.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/products.xml',
        'data/res_partner.xml',
        #'data/res.country.state.csv',
        #'views/res_config_settings_views.xml',
        'views/container_type_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/product_tlc_line.xml',
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        'views/account_journal_views.xml',
        'views/res_partner_views.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/res_config_settings.xml',
        'views/stock_move_line_views.xml',
        'views/internal_stock_transfer_views.xml',
        'views/stock_quant_views.xml',
        'wizard/access_model_wizard.xml',
        'views/ir_model_views.xml',
        'views/stock_orderpoint_views.xml',
        'views/website_sale_views.xml',
        'views/pos_config_view.xml',
        'views/pos_session_view.xml',
        'views/pos_payment_method_views.xml', #Add 17-06-2022
        'views/pos_payment_views.xml', #Add 17-06-2022
        'views/pos_order_views.xml', #Add 17-06-2022

        #'views/product_template_views.xml',

        # Assets
        'views/assets.xml',

        #WIZARD
        'wizard/sale_order_import_wizard.xml',
        'wizard/picking_import_wizard.xml',
        'wizard/stock_picking_update_wizard.xml',
        'wizard/account_payment_register_views.xml',
        'wizard/pos_coupon_apply_code_views.xml',
        'wizard/purchase_order_export_excel_wizard.xml',
        'wizard/message_seller_approval.xml',
        'wizard/orderpoint_rules_import_wizard.xml',
        'wizard/replacement_import_wizard.xml',
        'wizard/internal_transfer_import_wizard.xml',

        'views/view_inventory_imports.xml',
        #replaces
        'wizard/order_merge_wizard.xml',
        'wizard/picking_merge_wizard.xml',

        #REPORTS
        'reports/purchase_order_templates.xml',
        'reports/report_z_template.xml', #Add 06-06-2022

        #Comentado por el hecho de que solo sirvieron para pruebas.
        #'views/pos_order_views.xml',
    ],
    'qweb': [
            'static/src/xml/CouponPromotion.xml',
            'static/src/xml/OrderReceipt.xml',
            'static/src/xml/ReprintOrder.xml',
            'static/src/xml/PosOrdersAll.xml',
            'static/src/xml/FinancialEntityPopupWidget.xml',
             ],

}

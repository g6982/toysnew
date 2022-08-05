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
{
  "name"                 :  "Website Store Pickup",
  "summary"              :  """The module allows you to add physical store location on the website so the customers can pick up their order from their nearest location.""",
  "category"             :  "Website",
  "version"              :  "2.1.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Website-Store-Pickup.html",
  "description"          :  """Odoo Website Store Pickup
Locate store
Near me Seller address
Seller multiple address
Website store locator
Pick up order
Order pickup
Store order pickup
Website order
seller locations
Store physical location
Locate seller on map""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=website_store_pickup&custom_url=/store/locator",
  "depends"              :  [
                             'website_sale_delivery',
                             'website_store_locator',
                             'website_order_notes',
                            ],
  "data"                 :  [
                             'views/sale_shop_inherit_view.xml',
                             'views/res_config_view.xml',
                             'views/templates.xml',
                             'views/webkul_addons_config_inherit_view.xml',
                             'views/delivery_carrier_inherit_view.xml',
                             'data/pickup_set_default_values.xml',
                             'security/ir.model.access.csv',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  145,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}

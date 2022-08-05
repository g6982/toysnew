# Muk IT , muk_web_preview
# 山西清水欧度信息技术有限公司, Report Pdf Preview
# Sunpop.cn
# -*- coding: utf-8 -*-

# Created on 2019-09-02
# author: 广州尚鹏，https://www.sunpop.cn
# email: 300883@qq.com
# resource of Sunpop
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# Odoo12在线用户手册（长期更新）
# https://www.sunpop.cn/documentation/user/12.0/zh_CN/index.html

# Odoo12在线开发者手册（长期更新）
# https://www.sunpop.cn/documentation/12.0/index.html

# Odoo10在线中文用户手册（长期更新）
# https://www.sunpop.cn/documentation/user/10.0/zh_CN/index.html

# Odoo10离线中文用户手册下载
# https://www.sunpop.cn/odoo10_user_manual_document_offline/
# Odoo10离线开发手册下载-含python教程，jquery参考，Jinja2模板，PostgresSQL参考（odoo开发必备）
# https://www.sunpop.cn/odoo10_developer_document_offline/

##############################################################################
#    Copyright (C) 2009-TODAY Sunpop.cn Ltd. https://www.sunpop.cn
#    Author: Ivan Deng，300883@qq.com
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#    See <http://www.gnu.org/licenses/>.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
##############################################################################

{
    "name": "Report Direct Print. PoS print without iot box. Direct Preview without Download",
    'version': '14.20.06.10',
    'author': 'Sunpop.cn',
    'category': 'Base',
    'website': 'https://www.sunpop.cn',
    'license': 'LGPL-3',
    'sequence': 2,
    'price': 58.00,
    'currency': 'EUR',
    'images': ['static/description/banner.png'],
    'depends': [
        'web',
        'base_setup',
    ],
    'summary': """
    report direct print, pdf preview without download. Pdf direct print. html direct print Preview.
    POS auto print support. All odoo app like sale, purchase support.
    Notice!  Direct print only support chrome browser.
    """,
    'description': """    
    Support Odoo 14,13, Enterprise and Community Edition
    1. odoo Report direct print without iot box. pdf direct preview without download.
    2. pdf support, html report support.
    3. Can setup for default direct print or print after preview.
    4. Pos, point of sale support. All odoo app like sale, purchase support.
    5. Notice！  Direct print only support chrome browser.
    6. Multi-language Support.
    7. Multi-Company Support.
    8. Support Odoo 14,13, Enterprise and Community Edition
    ==========
    1. 直接报表打印，静默打印，无需设备支持。 pdf 无需下载直接预览
    2. PDF, html 格式支持
    3. 可配置是直接打印还是先预览再打印
    4. 收银POS支持
    5. 注意，只支持 chrome 浏览器
    6. 多语言支持
    7. 多公司支持
    8. Odoo 13, 企业版，社区版，多版本支持
    """,
    'data': [
        'views/assets.xml',
        'views/res_config_settings_views.xml',
        'data/ir_config_parameter.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

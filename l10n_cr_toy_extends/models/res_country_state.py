# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

NAMES = {
    '北京市': 'Beijing',
    '上海市': 'Shanghai',
    '浙江省': 'Zhejiang',
    '天津市': 'Tianjin',
    '安徽省': 'Provincia de Anhui',
    '福建省': 'Provincia de Fujian',
    '重庆市': 'Chongqing',
    '江西省': 'Provincia de Jiangxi',
    '山东省': 'Provincia de Shandong',
    '河南省': 'Provincia de Henan',
    '内蒙古自治区': 'Región Autónoma de Mongolia Interior',
    '湖北省': 'Provincia de Hubei',
    '新疆维吾尔自治区': 'Región Autónoma Uigur de Xinjiang',
    '湖南省': 'Provincia de Hunan',
    '宁夏回族自治区': 'Región Autónoma de Ningxia Hui',
    '广东省': 'Provincia de Guangdong',
    '西藏自治区': 'Región Autónoma del Tíbet',
    '海南省': 'Provincia de Hainan',
    '广西壮族自治区': 'Región Autónoma de Guangxi Zhuang',
    '四川省':  'Provincia de Sichuan',
    '河北省':'Provincia de Hebei',
    '贵州省': 'Provincia de Guizhou',
    '山西省': 'Provincia de Shanxi',
    '云南省': 'Provincia de Yunnan',
    '辽宁省': 'Provincia de Liaoning',
    '陕西省': 'Provincia de Shaanxi',
    '吉林省': 'Provincia de Jilin',
    '甘肃省': 'Provincia de Gansu',
    '黑龙江省': 'Provincia de Heilongjiang',
    '青海省': 'Provincia de Qinghai',
    '江苏省': 'Provincia de Jiangsu',
    '台湾省': 'Provincia de Taiwán',
    '香港特别行政区': 'Región Administrativa Especial de Hong Kong',
    '澳门特别行政区': 'Región Administrativa Especial de Macao'

}



class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    def init(self):
        res = super(ResCountryState, self).init()
        states = self.env['res.country.state'].sudo().search([])
        if states:
            for s in states:
                for k, v in NAMES.items():
                    if s.name == k:
                        s.name = v

        return res
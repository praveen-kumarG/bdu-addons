# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductUoM(models.Model):
    _inherit = 'product.uom'

    qty_rounding = fields.Boolean('Quantity Rounding', help="Check the quantity will be rounding off for report.")
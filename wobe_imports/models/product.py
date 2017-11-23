# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


PrintCategory = [('strook', 'Strook'),
                 ('stitching', 'Stitching'),
                 ('glueing', 'Glueing'),
                ]

class Product(models.Model):
    _inherit = "product.product"

    print_category = fields.Selection(PrintCategory, 'Print Category', help='Print/Booklet Category')

    @api.constrains('print_category')
    def _check_printCategory(self):
        for case in self:
            if case.print_category:
                if self.search([('print_category', '=', case.print_category), ('id','<>', case.id)]):
                    raise ValidationError(_('Product for this Print Category already exists'))
        return True

    _constraints = [
        (_check_printCategory, 'Already exists', []),
    ]

class ProductTemplate(models.Model):
    _inherit = "product.template"

    print_category = fields.Selection(PrintCategory, 'Print Category', related='product_variant_ids.print_category')
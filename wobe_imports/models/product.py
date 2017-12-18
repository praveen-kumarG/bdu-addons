# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp

PrintCategory = [('strook', 'Strook'),
                 ('stitching', 'Stitching'),
                 ('glueing', 'Glueing'),
                 ('plate_change', 'Plate Change'),
                 ('press_stop', 'Press Stop'),
                ]

class ProductTemplate(models.Model):
    _inherit = "product.template"

    print_category = fields.Selection(PrintCategory, 'Print Category')
    print_format_template = fields.Boolean('Print Format Template',
                                           help='Set True to assign Print Format to the Products')
    formats = fields.Selection([('MP', 'MP'), ('TB', 'TB'), ('BS', 'BS')], string='Paper Format')
    booklet_surface_area = fields.Float('Booklet Surface Area', help="Page surface booklet (newspaper) format in cm2",
                                        digits=dp.get_precision('Product Unit of Measure'))

    @api.constrains('print_format_template', 'formats')
    def _check_paperFormat(self):
        for case in self:
            if case.print_format_template:
                if self.search([('print_format_template', '=', True), ('formats','=', case.formats),
                                ('company_id', '=', case.company_id.id), ('id','<>', case.id)]):
                    raise ValidationError(_('Product for this Paper Format already exists'))
        return True

    _constraints = [
        (_check_paperFormat, 'Already exists', []),
    ]


class Product(models.Model):
    _inherit = "product.product"

    print_category = fields.Selection(PrintCategory, 'Print Category',
                                      related='product_tmpl_id.print_category',
                                      help='Print/Booklet Category')
    print_format_template = fields.Boolean('Print Format Template',
                                      related='product_tmpl_id.print_format_template',
                                      help='Set True to assign Print Format to the Products')
    formats = fields.Selection([('MP', 'MP'), ('TB', 'TB'), ('BS', 'BS')],
                                      related='product_tmpl_id.formats',
                                      string='Paper Format')



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

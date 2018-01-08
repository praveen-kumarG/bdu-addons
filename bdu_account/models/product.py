# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Product(models.Model):
    _inherit = "product.product"

    @api.multi
    def _name_var_get(self):
        '''Alternative name for variant name without [default_code]'''

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []
        for product in self.sudo():
            # display only the attributes with multiple possible values on the template
            variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped(
                'attribute_id')
            variant = product.attribute_value_ids._variant_name(variable_attributes)

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            res = (product.id, name)
            result.append(res)
        return result

    variant_name = fields.Char(compute='_name_var_get', string='Name including Variant Characteristics')
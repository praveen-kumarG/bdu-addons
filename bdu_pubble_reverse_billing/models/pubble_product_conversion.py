# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PubbleProductConversion(models.Model):
    _name        = 'pubble.product.conversion'
    _description = 'Translate Pubble product names and count into Odoo equivalent'

    @api.multi
    def _default_pubble_count_min(self) :
        return 1

    @api.multi
    def _default_pubble_count_max(self) :
        return 9999

    @api.multi
    def _default_count_conversion(self) :
        return True

    pubble_product_name = fields.Char('Pubble name',         required=True)
    pubble_count_min    = fields.Integer('Pubble min',       default=_default_pubble_count_min )
    pubble_count_max    = fields.Integer('Pubble max',       default=_default_pubble_count_max ) 
    count_conversion    = fields.Boolean('Tier product',     default=_default_count_conversion,
                                                             help="If true, range becomes one product") 
    odoo_product_id     = fields.Many2one('product.product', string='Odoo product', 
                                                             required=True)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True) :
        if 'pubble_count_min' in fields :
            fields.remove('pubble_count_min')
        if 'pubble_count_max' in fields :
            fields.remove('pubble_count_max')
        return super(PubbleProductConversion, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)


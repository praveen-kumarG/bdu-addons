# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Picking(models.Model):
    _inherit = 'stock.picking'

    order_id = fields.Many2one('sale.order', 'SO Number', ondelete='set null', index=True)

# -*- coding: utf-8 -*-
# Copyright 2017 Willem hulshof - <w.hulshof@magnus.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class productCategory(models.Model):
    _inherit = "product.category"

    complete_name = fields.Char(compute='_name_get_fnc', string='Name')
    date_type = fields.Selection([
            ('validity', 'Validity Date Range'),
            ('date', 'Date of Publication'),
            ('newsletter', 'Newsletter'),
            ('online', 'Online'),
            ('issue_date', 'Issue Date'),
        ], 'Date Type Advertising products')
    deadline_offset = fields.Integer('Hours offset from Issue Deadline', default=0)
    pubble = fields.Boolean('Ads go to Pubble')
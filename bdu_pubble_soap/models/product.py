# -*- coding: utf-8 -*-
# Copyright 2017 Willem hulshof - <w.hulshof@magnus.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class productCategory(models.Model):
    _inherit = "product.category"


    pubble = fields.Boolean('Ads to Pubble', default=False)
# -*- coding: utf-8 -*-
# Copyright 2017 Stephan ()
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.tools.translate import _


class res_partner(models.Model):
    _inherit = "res.partner"

    wobeauth = fields.Boolean(
        string=_("Wobe Geautoriseerd"),
        required=False,
        translate=False,
        readonly=False
    )

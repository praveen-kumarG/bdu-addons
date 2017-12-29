# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    job_id = fields.Many2one('wobe.job','Job Ref #',ondelete='set null', index=True)
    unit_amount = fields.Float('Quantity', default=0.0, digits=dp.get_precision('Paper Mass'))

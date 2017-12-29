# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    job_id = fields.Many2one('wobe.job','Job Ref #',ondelete='set null', index=True)
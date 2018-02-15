# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Picking(models.Model):
    _inherit = 'stock.picking'

    order_id = fields.Many2one('sale.order', 'SO Number', ondelete='set null', index=True)


class StockMove(models.Model):
    _inherit = "stock.move"

    analytic_account_id = fields.Many2one('account.analytic.account', compute='_compute_wobe_job', string='Analytic Account' ,help='Analytic Account associated to this move')
    job_id = fields.Many2one('wobe.job', compute='_compute_wobe_job',  string='Job Ref#', help='Job associated to this move')
    job_issue_date = fields.Date(related='job_id.issue_date', string='Job Issue Date', store=True)
    job_title = fields.Char(related='job_id.title', string='Job Title', store=True)


    def _compute_wobe_job(self):
        for move in self:
            if move.picking_id:
                move.job_id = self.env['wobe.job'].search([('picking_id', '=', move.picking_id.id)])
                if move.job_id:
                    move.analytic_account_id = self.env['account.analytic.account'].search([('name', '=', move.job_id.title)])
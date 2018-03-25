# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.queue_job.exception import FailedJobError


class AccountInvoiceConfirm(models.TransientModel):
    """
    This wizard will confirm the all the selected draft invoices if required via job queue
    """
    _inherit = "account.invoice.confirm"

    chunk_size = fields.Integer('Chunk Size Job Queue', default=50)
    job_queue = fields.Boolean('Process via Job Queue', default=False)

    @api.multi
    def invoice_confirm(self):
        if not self.job_queue:
            return super(AccountInvoiceConfirm, self).invoice_confirm()

        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        self.with_delay()._split_jobs(active_ids)

        return True

    @job
    def _split_jobs(self, inv_ids):
        size = self.chunk_size
        for x in xrange(0, len(inv_ids), size):
            chunk = inv_ids[x:x + size]
            self.with_delay().invoice_confirm_jobqueue(chunk)

    @job
    @api.multi
    def invoice_confirm_jobqueue(self, chunk):
        for record in self.env['account.invoice'].browse(chunk):
            if record.state not in ('draft', 'proforma', 'proforma2'):
                raise FailedJobError(_("Selected invoice(s) cannot be confirmed as they are not in 'Draft' or 'Pro-Forma' state."))
            record.action_invoice_open()

'''class AccountInvoiceCancel(models.TransientModel):
    """
    This wizard will cancel the all the selected invoices.
    If in the journal, the option allow cancelling entry is not selected then it will give warning message.
    """

    _name = "account.invoice.cancel"
    _description = "Cancel the Selected Invoices"

    @api.multi
    def invoice_cancel(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['account.invoice'].browse(active_ids):
            if record.state in ('cancel', 'paid'):
                raise UserError(_("Selected invoice(s) cannot be cancelled as they are already in 'Cancelled' or 'Done' state."))
            record.action_invoice_cancel()
        return {'type': 'ir.actions.act_window_close'}'''

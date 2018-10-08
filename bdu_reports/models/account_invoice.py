# -*- coding: utf-8 -*-
import logging, pdb
from odoo import api, fields, exceptions, models


class AccountInvoiceWithAccountManager(models.Model):
    _inherit = 'account.invoice'
    account_manager_id = fields.Many2one('res.users', string='Account manager')

    @api.multi
    def compute_account_manager(self):
        if self.partner_id.user_id :	
            return self.partner_id.user_id.id
        else :
            if self.partner_id.parent_id.user_id :
               return self.partner_id.parent_id.user_id.id
            else :
               return False

    @api.model
    def create(self, vals):
        am =self.compute_account_manager()
        if am :
            vals['account_manager_id']= am
        return super(AccountInvoiceWithAccountManager,self).create(vals)

    @api.model
    def write(self, vals):
        am =self.compute_account_manager()
        if am :
            vals['account_manager_id']= am
        return super(AccountInvoiceWithAccountManager,self).write(vals)

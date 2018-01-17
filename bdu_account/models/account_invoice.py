# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = ["account.invoice"]

#    published_customer = fields.Many2one('res.partner', 'Advertiser', domain=[('customer','=',True)])


    # TODO: check if this is needed?
    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'account.report_invoice')

class AccountInvoiceLine(models.Model):
    _inherit = ["account.invoice.line"]

    @api.model
    def create(self, vals):
        ctx = self.env.context.copy()
        line_obj = super(AccountInvoiceLine, self).create(vals)
        if 'active_model' in ctx:
            if ctx.get('active_model') in ('sale.order','sale.order.line'):
                for sale_line_obj in line_obj.sale_line_ids:
                    description = False
                    if sale_line_obj.company_id.use_bduprint and line_obj.product_id == sale_line_obj.product_id and sale_line_obj.product_id.product_tmpl_id.invoice_description:
                        description = sale_line_obj.name
                    if description:
                        line_obj.write({'name':description})
        return line_obj


#    so_number = fields.Char(string='Order Number')
#    sol_issuedt = fields.Date(string='Issue Date')
#    sol_title = fields.Char(string='Title')
#    sol_discount = fields.Float(string='Discount', digits=dp.get_precision('Account'))
#    sol_computed_discount = fields.Float(string='Computed Discount', digits=dp.get_precision('Account'))

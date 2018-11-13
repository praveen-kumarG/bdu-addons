# -*- coding: utf-8 -*-
import datetime, pdb
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class history_order(models.Model):
    _name        = 'history.order'
    _description = 'History of orders from previous administration'

    order_type   = fields.Char('Type')                      #advertisement, subscription, folder, online
    source       = fields.Char('Source')
    order        = fields.Integer('Order')
    orderline    = fields.Char('Orderline')
    advertiser_id= fields.Integer('Advertiser id')
    advertiser   = fields.Char('Advertiser', index=True)
    debtor_id    = fields.Integer('Debtor id')
    debtor       = fields.Char('Debtor', index=True)
    contact_id   = fields.Integer('Contact id')
    contact      = fields.Char('Contact')
    salesteam    = fields.Char('Sales team')
    salesperson  = fields.Char('Sales person')

    product      = fields.Char('Product')
    adv_category = fields.Char('Adv. category')
    page_category= fields.Char('Page category')
    issue_code   = fields.Char('Issue')
    title        = fields.Char('Title')
    issue_date   = fields.Date('Issue date')
    issue_year   = fields.Integer('Issue year')
    issue_month  = fields.Integer('Issue month')
    issue_day    = fields.Integer('Issue day')
    issue_week   = fields.Integer('Issue week')
    issue_weekday= fields.Integer('Issue weekday')

    list_price   = fields.Float('List price')
    net_price    = fields.Float('Net price')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True) :
        if 'order' in fields :
            fields.remove('order')
        if (not 'issue_year' in groupby) and 'issue_year' in fields :
            fields.remove('issue_year')
        if (not 'issue_month' in groupby) and 'issue_month' in fields :
            fields.remove('issue_month')
        if (not 'issue_day' in groupby) and'issue_day' in fields :
            fields.remove('issue_day')
        if (not 'issue_week' in groupby) and'issue_week' in fields :
            fields.remove('issue_week')
        if (not 'issue_weekday' in groupby) and'issue_weekday' in fields :
            fields.remove('issue_weekday')
        if (not 'issue_weekday' in groupby) and'issue_weekday' in fields :
            fields.remove('issue_weekday')
        return super(history_order, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    

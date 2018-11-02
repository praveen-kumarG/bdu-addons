# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PubbleProductionData(models.Model):
    _name            = 'pubble.production.data'
    _description     = 'Collected Pubble production data'

    #billing line belongs to one article with article attributes
    article_id        = fields.Integer('Article')
    product_id        = fields.Many2one('product.product',              string='Product')
    count             = fields.Integer('Count')
    freelancer        = fields.Many2one('res.partner',                  string='Freelancer')
    url               = fields.Char('Url')
    remark            = fields.Char('werktitel')

    #first issue (hence ou) reported takes the costs, other publications administered for reference
    issue_id          = fields.Many2one('sale.advertising.issue',       string='Issue')
    analytic_account_id   = fields.Many2one('account.analytic.account', string='Analytic account', store=True)
    operating_unit_id = fields.Many2one('operating.unit',               string='Operating Unit')
    issue_ids         = fields.Many2one('sale.advertising.issue',       string='Issues')
  
    #time stamp : first issue has preference over time of acceptance, locked after processed
    year              = fields.Integer('Year')
    week              = fields.Integer('Week')

    #empty, one or more
    commissioned_by   = fields.Char('Commissioned by') #Many2one('res.partner',              string='Commissioned by')

    #status fields
    accepted          = fields.Boolean('OK')
    processed         = fields.Boolean('Processed')

    #unique reference,
    key               = fields.Char(compute="compute_key",              string='Unique key') 
    _sql_constraints  = [('Article & product combined', 'unique(key)', 'Article ID and product already defined. Should be unique.' )]

    
    @api.multi
    @api.depends('article_id', 'product_id')
    def compute_prod_cat(self):
        key = str(article_id)+"-"+str(product)
        return

    @api.multi
    @api.depends('accepted')
    def toggle_accepted(self) :
        if accepted :
            #todo: 
            self.year=2018
            self.week=42
        else :
            if not issue_id :
                self.year=False
                self.week=False
        return


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True) :
        #do not sum year and week fields
        if 'year' in fields :
            fields.remove('year')
        if 'week' in fields :
            fields.remove('week')
        return super(mis_pubble_kpi, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

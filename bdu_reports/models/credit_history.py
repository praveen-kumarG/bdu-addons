# -*- coding: utf-8 -*-
import datetime, pdb
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class credit_history(models.Model):
    _name        = 'credit.history'
    _description = 'History of open invoices per customer, account manager and week'
    year         = fields.Integer('Year')
    week         = fields.Integer('Week')
    partner_id   = fields.Many2one('res.partner',        string='Partner')
    user_id      = fields.Many2one('res.users',          string='Account manager')
    crm_team_id  = fields.Many2one('crm.team',           string='Salesteam')
    at_lte8d     = fields.Float('Tot. =<8d')
    res_lte8d    = fields.Float('Res. =<8d')
    at_lte35d    = fields.Float('Tot. =<35d')
    res_lte35d   = fields.Float('Res. =<35d')
    at_gt35d     = fields.Float('Tot. >35d')
    res_gt35d    = fields.Float('Res. >35d')
    amount_total = fields.Float('Total')
    residual     = fields.Float('Residual')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True) :
        if (not 'year' in groupby) and 'year' in fields :
        	fields.remove('year')
        if (not 'week' in groupby) and 'week' in fields :
            fields.remove('week')
        return super(credit_history, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.multi
    def weekly_fill(self) :
        #calc this week for timestamping
        now  = datetime.date.today()
        year = now.isocalendar()[0]
        week = now.isocalendar()[1]

        #target data
        ch = self.search([])

        #source data
        #groupby    =['date_due','account_manager_id','partner_id']
        #sumfields  =['amount_total','residual']
        open_invoices = self.env['account.invoice'].search([  ('state','=','open'),   ('type','in',('out_invoice', 'out_refund','customer_invoice','customer_refund'))  ])
        
        #accumulate per partner within date ranges relative to due date
        d = {}
        for oi in open_invoices :
            partner_id= oi['partner_id'].id
            #care for when dunning strategy is missing
            if oi['date_due'] :
                date_due  = datetime.datetime.strptime(oi['date_due'],DEFAULT_SERVER_DATE_FORMAT).date()
            else :
                date_due  = datetime.datetime.strptime(oi['date_invoice'],DEFAULT_SERVER_DATE_FORMAT).date()
            days      = (now - date_due).days
            at_lte8d  = at_lte35d  = at_gt35d = 0
            res_lte8d = res_lte35d = res_gt35d = 0

            if days>0 and days <=8 :
                at_lte8d   = oi['amount_total']
                res_lte8d  = oi['residual']
            elif days>8 and days <=35 : 
                at_lte35d  = oi['amount_total']
                res_lte35d = oi['residual']
            elif days>35 :
                at_gt35d   = oi['amount_total']
                res_gt35d  = oi['residual']

            if partner_id in d :
                d[partner_id]['at_lte8d']     += at_lte8d
                d[partner_id]['res_lte8d']    += res_lte8d
                d[partner_id]['at_lte35d']    += at_lte35d
                d[partner_id]['res_lte35d']   += res_lte35d
                d[partner_id]['at_gt35d']     += at_gt35d
                d[partner_id]['res_gt35d']    += res_gt35d
                d[partner_id]['amount_total'] += at_lte8d  + at_lte35d + at_gt35d
                d[partner_id]['residual']     += res_lte8d + res_lte35d + res_gt35d
            else :
                d[partner_id] = { 'year'        : year,
                                  'week'        : week,
                                  'partner_id'  : partner_id,
                                  'at_lte8d'    : at_lte8d,
                                  'res_lte8d'   : res_lte8d,
                                  'at_lte35d'   : at_lte35d,
                                  'res_lte35d'  : res_lte35d,
                                  'at_gt35d'    : at_gt35d,
                                  'res_gt35d'   : res_gt35d,
                                  'amount_total': at_lte8d  + at_lte35d  + at_gt35d,
                                  'residual'    : res_lte8d + res_lte35d + res_gt35d
                                 }
            #for backward compatibility; if account manager is missing it will not overwrite good info
            if oi['account_manager_id'] :
                d[partner_id]['user_id']=oi['account_manager_id'].id
                d[partner_id]['crm_team_id']=self.env['crm.team'].search([('member_ids','=',oi['account_manager_id'].id)]).id

        #add or change record in target data
        for key in d :
            partner_record = d[key]
            existing_recs = ch.search([  ('year',      '=', partner_record['year']       ),
                                         ('week',      '=', partner_record['week']       ),
                                         ('partner_id','=', partner_record['partner_id'] )
                                     ])     
            if len(existing_recs)==0 :
                ch.create(partner_record)
            else :
                existing_recs[0].write(partner_record)


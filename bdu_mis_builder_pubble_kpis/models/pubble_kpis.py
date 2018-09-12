# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mis_pubble_kpi(models.Model):
	_name        = 'mis.pubble.kpi'
	_description = 'Collected Pubble page data'
	title        = fields.Char('Title',        required=False)
	title_code   = fields.Char('Title code',   required=False)
	issue_date   = fields.Date('Issue date',   required=True)  
	page_type    = fields.Char('Page type')
	page_nr      = fields.Integer('Page nr',   required=True)
	page_style   = fields.Char('Page style')
	is_spread    = fields.Boolean('Spread',    required=True) 
	is_inherited = fields.Boolean('Inherited', required=True)
	ad_count     = fields.Integer('Ad count',  required=True)
	ad_page      = fields.Integer('Ad page',   required=True)
	ed_page      = fields.Integer('Ed page',   required=True)

	company_id            = fields.Many2one('res.company',              string='Company')
	analytic_account_id   = fields.Many2one('account.analytic.account', string='Analytic account', store=True)
	operating_unit_id     = fields.Many2one('operating.unit',           string='Operating Unit')

	@api.model
	def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True) :
		if 'page_nr' in fields :
			fields.remove('page_nr')
		return super(mis_pubble_kpi, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
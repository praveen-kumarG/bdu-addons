# -*- coding: utf-8 -*-
import pdb
import datetime
from odoo import api, fields, models



    

class ProductAnnouncementOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def compute_today(self) :
    	return datetime.date.today()

    def compute_end_of_time(self) :
    	return datetime.date(2099,12,31)
    
    #meta tags for announcement database on website
    announcement_firstname     = fields.Char('First name')
    announcement_lastname      = fields.Char('Last name')
    announcement_city          = fields.Char('Place')
    announcement_from_date     = fields.Date('Show online from', default=compute_today)
    announcement_to_date       = fields.Date('Show online until', default=compute_end_of_time)
    announcement_adv_issue_ids = fields.Many2many('sale.advertising.issue', string='Publiced in')



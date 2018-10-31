# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models



    

class ProductAnnouncementOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    #meta tags for announcement database on website
    firstname    = fields.Char('First name')
    lastname     = fields.Char('Last name')
    city         = fields.Char('Place')

# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models

    

class ProductTemplateDistribution(models.Model):
    _inherit = 'product.template'
    
    custom_orderline = fields.Selection(selection_add=[('Distribution','Distribution')]) 
 

class ProductCategoryDistribution(models.Model):
    _inherit = 'product.category'
    
    #successive products may append to the selection list
    custom_orderline = fields.Selection(selection_add=[('Distribution','Distribution')])

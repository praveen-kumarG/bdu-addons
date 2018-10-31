# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models

    

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    #successive products may append to the selection list
    prod_cat = fields.Selection([], string="Customize for") 


class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    #successive products may append to the selection list
    prod_cat = fields.Selection([], string="Customize for") 


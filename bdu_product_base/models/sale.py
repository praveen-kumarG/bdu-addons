# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models

product_base_inhibit_onchange = False

    

class ProductBaseOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    main_cat_id = fields.Many2one('product.category', string='Main category')
    prod_cat    = fields.Char(compute="compute_prod_cat", string='Product category') 

    #product category triggers orderline behaviour
    @api.multi
    @api.depends('product_id')
    def compute_prod_cat(self):
        global product_base_inhibit_onchange
        if product_base_inhibit_onchange :
            return
        for record in self:
            product_base_inhibit_onchange=True
            #set custom handling
            if record.product_id :
                if record.product_id.product_tmpl_id.prod_cat : 
                    record.prod_cat = record.product_id.product_tmpl_id.prod_cat
                else :
                    if record.product_id.product_tmpl_id.categ_id :
                        record.prod_cat = record.product_id.product_tmpl_id.categ_id.prod_cat
                    else :
                        record.prod_cat = False
            else :
                record.prod_cat = False   
            #call parent, parent expects a singleton
            super(ProductBaseOrderLine, record).product_id_change()
            product_base_inhibit_onchange=False
        return 


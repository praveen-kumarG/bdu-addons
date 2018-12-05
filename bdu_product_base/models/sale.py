# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models


    

class ProductBaseOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    custom_orderline  = fields.Char(compute="set_custom_orderline", string='Custom orderline',  store=True) 

    @api.multi
    @api.depends('product_id')
    def set_custom_orderline(self):
        #singleton when editing orderline, recordset when saving order
        for record in self :
            if record.product_id :
                if record.product_id.product_tmpl_id.custom_orderline : 
                    record.custom_orderline = record.product_id.product_tmpl_id.custom_orderline
                else :
                    if record.product_id.product_tmpl_id.categ_id :
                        record.custom_orderline = record.product_id.product_tmpl_id.categ_id.custom_orderline
                    else :
                        record.custom_orderline = False
            else :
                record.custom_orderline = False       
        return 


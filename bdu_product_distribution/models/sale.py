# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models



    

class ProductDistributionOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    area_id     = fields.Many2one('logistics.address.table',  string='Distribution areas')
    area_ids    = fields.Many2many('logistics.address.table', string='Distribution areas')
    distributor = fields.Many2one('res.partner',              string='Distributor')

    #ordered quantity is update to becomen either total of single area or total of multiple areas
    @api.model
    @api.onchange('area_id','area_ids')
    def area_change(self):
        if not self.prod_cat == u'Distribution' :
            return
        if self.area_ids :
            product_uom_qty = 0;
            for area in self.area_ids :
                product_uom_qty += area.folder_addresses
        else :
            product_uom_qty = area_id.folder_addresses
        self.product_uom_qty = (float(product_uom_qty) / 1000)
        return 
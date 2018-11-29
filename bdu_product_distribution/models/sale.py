# -*- coding: utf-8 -*-
import datetime, pdb
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ProductDistributionOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    #note, re-use in form view of existing fields leaves one them empty, hence product specific fields
    distribution_area_ids    = fields.Many2many('logistics.address.table', string='Distribution areas')
    distribution_item        = fields.Char('Item to distribute')
    distribution_count_all   = fields.Boolean('All addresses')
    distribution_central     = fields.Boolean('Central distribution') #additional to carrier_id to circumvent hard coding of delivery method
    distribution_from_date   = fields.Date('Distribute from')
    distribution_to_date     = fields.Date('Distribute to')


    #ordered quantity is updatee to either total of all addresses or only folder addresses area
    @api.model
    @api.onchange('distribution_area_ids','distribution_count_all')
    def set_distribition_uom_qty(self):
        if not self.custom_orderline == u'Distribution' :
            return
        if self.distribution_area_ids :
            fa = 0;
            ta = 0;
            for area in self.distribution_area_ids :
                fa += area.folder_addresses
                ta += area.total_addresses
            if self.distribution_count_all :
                self.product_uom_qty = ta
            else :
                self.product_uom_qty = fa            
            self.product_uom_qty = (float(self.product_uom_qty) / 1000)
        else :
            self.product_uom_qty = 0
        return 

    #data input help when accessed for first time
    @api.onchange('distribution_from_date') 
    def distribution_from_date_onchange(self) :
        if self.distribution_from_date and self.distribution_to_date == False :
            from_date=datetime.datetime.strptime(self.distribution_from_date,DEFAULT_SERVER_DATE_FORMAT).date()
            self.distribution_to_date = from_date+datetime.timedelta(days=7)
        return

    #helper for appendix report
    @api.model
    def sum_by_distributor(self):
        summary = self.distribution_area_ids.read_group([('id','in',self.distribution_area_ids.ids)],['user_id','user_id.street','folder_addresses','total_addresses'],['user_id'])
        total_result=[]
        for entry in summary :
            result={}
            if entry['user_id'] : 
                user    = self.env['res.users'].browse(entry['user_id'][0])
                partner = user.partner_id
                result  = {
                    'user_id'   : user.id,
                    'partner_id': partner.id,
                    'name'      : partner.name,
                    'street'    : (partner.street or '-'),
                    'zip'       : (partner.zip  or '-'),
                    'city'      : (partner.city or '-'),
                    'phone'     : (partner.phone or '-')
                }
            else :
                result = {
                    'user_id'   : False,
                    'partner_id': False,
                    'name'      : "Nader te bepalen",
                    'street'    : "-",
                    'zip'       : "-",
                    'city'      : "-",
                    'phone'     : "-"
                }
            result['total_addresses']  = entry['total_addresses']
            result['folder_addresses'] = entry['folder_addresses']
            total_result.append(result)
        return total_result

    #helper for report "list for distributors"
    @api.model 
    def list_for_distributors(self) :
        distributors = self.sum_by_distributor() 
        for distributor in distributors :
            areas = self.distribution_area_ids.search_read([('id','in',self.distribution_area_ids.ids),('user_id', '=',distributor['user_id'])])
            distributor['areas'] =areas
        return distributors


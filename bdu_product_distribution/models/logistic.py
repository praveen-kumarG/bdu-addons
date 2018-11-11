# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models

class LogisticsAdressTable(models.Model):
    _inherit='logistics.address.table' 

    zip_2    = fields.Char(string='Zip AB')
    nr_from  = fields.Integer(string='From streetnr.')
    nr_until = fields.Integer(string='Until streetnr.') #and including
    #when used as exceptions: use negative numbers for folder_addresses and total_addresses
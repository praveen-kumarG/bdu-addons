# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Magnus 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = 'res.company'

    report_background_image1 = fields.Binary('Background Image for Report Frontpage',
            help='Set Background Image for Report Frontpage')

    report_background_image2 = fields.Binary('Background Image for Report Following Pages',
            help='Set Background Image for Report Following Pages')

    use_bduprint = fields.Boolean('Use BDUprint Layout?', help="Set 'True' to print the Invoice as per BDUprint layout.")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

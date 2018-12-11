# -*- encoding: utf-8 -*-
##############################################################################
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs.
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company like Veritos.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

{
    'name'       : 'BDU advertising sales',
    'version'    : '10.0.1.1.0',
    'category'   : 'sale',
    'description': """
BDU specific modifications:

a) filters and grouping in sale advertising: complete replacement of standard set\n
b) title grouping by primary salesteam added to facilitate filtering based on titles\n
The latter based on sales teams to circumvent additional administration\n
Note that by using sales teams only direct sales teams should be used (i.e. one channel)\n
Note that results from title based filtering may differ from salesteam filter as salesperson might sell titles belonging to other teams. 


    """,
    'author'  	 : 'D. Prosee',
    'website' 	 : 'http://www.bdu.nl',
    'depends' 	 : [
    				'sale_advertising_order',
                    #'bdu_crm',
    			   ],
    'data'    	 : [
		            "data/mail_template_data.xml",
		            "views/sale_advertising_order_line_filter_view.xml",
                    "views/sale_advertising_issue_form_view.xml",
    			   ],
    'demo'    	 : [
    			   ],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


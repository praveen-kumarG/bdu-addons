# -*- coding: utf-8 -*-
{
    'name': "BDU product announcement",

    'summary': """
        Order enhancements for product (family) announcements
                """,

    'description': """
        Product announcement enhancements include:\n
        - no product variant selection enhancement (not needed)\n
        - custom handling on orderline form\n\n

        Usage:\n
        - define products within custom handling \'Announcement\' , found on product tab \'Sale\'\n
        - or organize products under a product category with mentioned custom handling \n
        - the custom handling on the product (template) takes precedence over the one mentioned in the product category\n
        - custom fields will show on orderline after selection of product

    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 
    'category': 'sale',
    'version' : '10.0',
    'depends' : [
                 'bdu_product_base',
                 'sale_advertising_order',
                ],
    'data'    : [
                 #'security/security.xml',
                 #'security/ir.model.access.csv',
                 'views/orderline_adaptions.xml',
                 'views/announcement.xml'
                ],
    'demo'    : [
                ],
}
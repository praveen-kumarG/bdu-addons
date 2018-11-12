# -*- coding: utf-8 -*-
{
    'name': "BDU product distribution",

    'summary': """
        Order enhancements for product category distribution
                """,

    'description': """
        Product distribution enhancements include:\n
        - no product variant selection enhancement (not needed)\n
        - custom handling on orderline form\n
        - selected area(s) and distributor added to sale orderline\n
        - quantity ordered calculated on logistics table, divided by 1000\n\n
        Usage:\n
        - define products within custom handling \'Distribution\' , found on product tab \'Sale\'\n
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
                 'folders',
                ],
    'data'    : [
                 #'security/security.xml',             #no additional models
                 #'security/ir.model.access.csv',      #no additional models
                 'reports/appendix_distribution.xml',
                 'reports/list_for_distributors.xml',
                 'views/orderline_adaptions.xml',
                 'views/distribution.xml'
                ],
    'demo'    : [
                ],
}
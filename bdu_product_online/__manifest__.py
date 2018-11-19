# -*- coding: utf-8 -*-
{
    'name': "BDU product online",

    'summary': """
        Order enhancements for Online products
                """,

    'description': """
        Product online enhancements include:\n
        - no product variant selection enhancement (not needed)\n
        - custom handling on orderline form for:\n
           * Display bannering,\n 
           * Social advertising,\n
           * Video advertising \n\n

        Usage:\n
        - define products within custom handling \'Online\' , found on product tab \'Sale\'\n
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
                 'security/security.xml',
                 'security/ir.model.access.csv',
                 'views/orderline_adaptions.xml',
                 'views/online.xml',
                 'views/profile.xml',
                 'data/project.xml',
                 'data/target_profiles.xml',
                ],
    'demo'    : [
                ],
}
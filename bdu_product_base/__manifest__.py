# -*- coding: utf-8 -*-
{
    'name': "BDU custom product base",

    'summary': """
        Base for custom product handling
                """,

    'description': """
        Provisions infrastructure for custom product handlings on the orderline.\n
        Specific handling is defined by a \'Product procedure\' on either product template or product category level.\n 
        Definition on product (template) level takes precedence over a definition on product category level.\n
        \n
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 
    'category': 'sale',
    'version' : '10.0',
    'depends' : [
                 'sale',
                 'product',
                ],
    'data'    : [
                 'views/sale.xml',
                 'views/product.xml'
                ],
    'demo'    : [
                ],
}
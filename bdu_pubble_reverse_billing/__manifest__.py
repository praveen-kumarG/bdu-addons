# -*- coding: utf-8 -*-
{
    'name': "BDU Pubble reverse billing",

    'summary': """
        Collect Pubble information and use for reverse billing.
        """,

    'description': """
        Collect editor's and photographer's results from Pubble into Odoo.\n
        Present info to facilitate audit by content manager.\n
        Groups info by chief editor (additional field on advertising issues).\n
        Convert admitted info into reverse billing invoice lines.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 

    'category': 'Reporting',
    'version': '10.0',

    # depends on mis_builder to find menu location (see views)
    'depends': ['base',
                'sale_advertising_order',     #to group titles based on chief editor
                'reverse_billing'
               ],

    # always loaded
    'data': [
        #'security/security.xml',
        #'security/ir.model.access.csv',
        'views/pubble_reverse_billing_config.xml',
        'views/pubble_reverse_billing_info.xml',
    ],
    'demo': [
        'demo/config.xml',
    ],
    
}
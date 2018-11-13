# -*- coding: utf-8 -*-
{
    'name': "BDU Peacock",

    'summary': """
        Sends movelines and account info
                """,

    'description': """
        BDU accountant Schuiteman / Peacock insights use periodic accounting info to monitor data quality.\n
        This interface collects and ships this information.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 
    'category': 'Connector',
    'version' : '10.0',
    'depends' : ['account'
                ],
    'data'    : [
                 'security/security.xml',
                 'security/ir.model.access.csv',
                 'views/peacock_config.xml',
                ],
    'demo'    : [
                 #'demo/demo.xml',
                ],
}
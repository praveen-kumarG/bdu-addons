# -*- coding: utf-8 -*-
{
    'name': "BDU reports",

    'summary': """
        BDU specific reports. 
                """,

    'description': """
        Reports: <br/>
        - draft invoices without address\n
        - invoice amounts and account manager
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3",     
    'category': 'Reporting',
    'version' : '10.0',
    'depends' : ['base', 
                ],
    'data'    : [
                  'reports/qa_reports.xml',
                ],
    'demo'    : [
                ],
}
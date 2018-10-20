# -*- coding: utf-8 -*-
{
    'name': "BDU reports",

    'summary': """
        BDU specific reports. 
                """,

    'description': """
        Reports: \n
        - draft invoices without address (print action on selected invoices)\n
        - invoice amounts and account manager (print action on selected invoices)\n
        - tree, graph, pivot on open invoice history (menu item)
        - method to consolidate current (weekly) status (to be called by a scheduled action)\n
        - history of orders presented under Dashboard/History
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3",     
    'category': 'Reporting',
    'version' : '10.0',
    'depends' : [
                 'account_operating_unit', 
                ],
    'data'    : [
                  'security/security.xml',
                  'security/ir.model.access.csv',
                  'reports/qa_reports.xml',
                  'views/credit_history.xml',
                  'views/history_order.xml',
                ],
}
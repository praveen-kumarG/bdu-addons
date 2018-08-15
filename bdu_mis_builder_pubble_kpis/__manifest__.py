# -*- coding: utf-8 -*-
{
    'name': "BDU MIS builder collector of Pubble KPIs",

    'summary': """
        Collect KPI information from Pubble for MIS builder reports""",

    'description': """
        Collect KPI's from Pubble into Odoo so MIS builder can use them in MIS reports.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Reporting',
    'version': '0.1',

    # depends on mis_builder to find menu location (see views)
    'depends': ['base', 'mis_builder'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/pubble_config.xml',
        'views/pubble_kpis.xml'
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
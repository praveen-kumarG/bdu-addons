# -*- coding: utf-8 -*-
{
    'name': "BDU Pubble reverse billing",

    'summary': """
        Collect Pubble information and use for reverse billing.
        """,

    'description': """
        Collect editor's and photographer's results from Pubble into Odoo.\n
        Freelancers must have one (and only one) matching email address in res.partner and must be a supplier.\n
        Contributors with an email address containing "@bdu.nl" will be skipped.\n
        Collected info will be presented together with commissioning, publication and sibling work to facilitate easy auditing by content manager.\n
        Several filters and grouping options added as well as a pivot view to check against budgets.\n
        Accepted work, indicated by a checkbox, will not accept additional updates. Unchecking makes updating available again.\n
        Accepted work may be selected and push to Finance as a SOW batch (action from the action menu).After pushing to SOW batch one cannot uncheck anymore.\n
        Separate security groups support editors and application managers without the need for access to reverse_billing.\n
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
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/pubble_reverse_billing_config.xml',
        'views/pubble_reverse_billing_info.xml',
        'views/pubble_product_conversion.xml',
        'views/reverse_billing.xml'
    ],
    'demo': [
        'demo/config.xml',
    ],
}


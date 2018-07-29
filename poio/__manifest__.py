# -*- coding: utf-8 -*-
{
    'name': "Promille order interface => Odoo (POIO)",

    'summary': """
        Collect orders from Promille""",

    'description': """
        Collect Promille orders, create or update into Odoo with corresponding partners.
        Orders are identied at order header level with promille_order_id.
        Orderlines are identified at orderline level by ad_number using promille order number, ad_id and title.
    """,

    'author'  : "D. Prosee",
    'website' : "http://www.bdu.nl",
    'license' : "LGPL-3", 

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Website',
    'version': '0.1',

    # depends on module sale to find menu location (see views)
    # to fill res.partner attribute coc_registration_number module res partner_coc is required
    # m.m. res.partner attribute sector_id requires module partner_sector
    # m.m. res.partner attribute is_ad_agency requires module bdu_account
    # m.m. res.partner attribute promille_id requires module sale_advertising_order (already required by bdu_account)
    # NB since bdu_account needs product.template attribute booklet_surface_area, but without depends, module wobe_imports is also needed
    'depends': ['base', 'sale', 'partner_coc', 'partner_sector', 'wobe_imports', 'bdu_account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/poio_menu.xml',
        'views/poio_config.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/config.xml',
    ],
}
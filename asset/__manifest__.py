# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2020 CodUP (<http://codup.com>).
#
##############################################################################

{
    'name': 'Assets',
    'version': '17.0.1.0',
    'summary': 'Asset Management',
    'description': """
Managing Assets in Odoo.
===========================
Support following feature:
    * Location for Asset
    * Assign Asset to employee
    * Track warranty information
    * Custom states of Asset
    * States of Asset for different team: Finance, Warehouse, Manufacture, Maintenance and Accounting
    * Drag&Drop manage states of Asset
    * Asset Tags
    * Search by main fields
    """,
    'author': 'CodUP',
    'website': 'http://codup.com',
    'license': 'AGPL-3',
    'category': 'Industries',
    'sequence': 0,
    'depends': ['stock'],
    'demo': ['data/asset_demo.xml'],
    'data': [
        'security/asset_security.xml',
        'security/ir.model.access.csv',
        'views/asset_view.xml',
        'data/asset_data.xml',
        'data/stock_data.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "asset/static/src/css/asset.css",
        ]
    },
    'installable': True,
    'application': True,
}

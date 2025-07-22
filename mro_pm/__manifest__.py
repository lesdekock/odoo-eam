# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2020 CodUP (<http://codup.com>).
#
##############################################################################

{
    'name': 'MRO PM',
    'version': '17.0.1.0',
    'summary': 'Asset Proactive Maintenance',
    'description': """
Manage Proactive Maintenance process in OpenERP
=====================================

Asset Maintenance, Repair and Operation.
Add support for Proactive Maintenance.

Main Features
-------------
    * Meter Management for Asset
    * Planning Maintenance Work Orders base on Meters
    * PM Rules for Assets by Tag

Required modules:
    * asset
    * mro
    """,
    'author': 'CodUP',
    'website': 'http://codup.com',
    'license': 'AGPL-3',
    'category': 'Industries',
    'sequence': 0,
    'depends': ['mro'],
    'demo': ['data/mro_pm_demo.xml'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/replan_view.xml',
        'views/mro_pm_view.xml',
        'data/mro_pm_sequence.xml',
        'views/asset_view.xml',
    ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

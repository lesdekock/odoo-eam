# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2015-2016 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import models, fields


class AssetAsset(models.Model):
    _inherit = 'asset.asset'
    
    name = fields.Char(tracking=True)
    finance_state_id = fields.Many2one(tracking=True)
    warehouse_state_id = fields.Many2one(tracking=True)
    manufacture_state_id = fields.Many2one(tracking=True)
    maintenance_state_id = fields.Many2one(tracking=True)
    maintenance_state_color = fields.Selection(tracking=True)
    criticality = fields.Selection(tracking=True)
    property_stock_asset = fields.Many2one(tracking=True)
    active = fields.Boolean(tracking=True)
    asset_number = fields.Char(tracking=True)
    model = fields.Char(tracking=True)
    serial = fields.Char(tracking=True)
    vendor_id = fields.Many2one(tracking=True)
    manufacturer_id = fields.Many2one(tracking=True)
    start_date = fields.Date(tracking=True)
    purchase_date = fields.Date(tracking=True)
    warranty_start_date = fields.Date(tracking=True)
    warranty_end_date = fields.Date(tracking=True)

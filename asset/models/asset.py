# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2020 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models
from odoo import tools

STATE_COLOR_SELECTION = [
    ('0', 'Red'),
    ('1', 'Green'),
    ('2', 'Blue'),
    ('3', 'Yellow'),
    ('4', 'Magenta'),
    ('5', 'Cyan'),
    ('6', 'Black'),
    ('7', 'White'),
    ('8', 'Orange'),
    ('9', 'SkyBlue')
]


class AssetState(models.Model):
    """ 
    Model for asset states.
    """
    _name = 'asset.state'
    _description = 'State of Asset'
    _order = "sequence"

    STATE_SCOPE_TEAM = [
        ('0', 'Finance'),
        ('1', 'Warehouse'),
        ('2', 'Manufacture'),
        ('3', 'Maintenance'),
        ('4', 'Accounting')
    ]

    name = fields.Char('State', size=64, required=True, translate=True)
    sequence = fields.Integer('Sequence', help="Used to order states.", default=1)
    state_color = fields.Selection(STATE_COLOR_SELECTION, 'State Color')
    team = fields.Selection(STATE_SCOPE_TEAM, 'Scope Team')

    def change_color(self):
        color = int(self.state_color) + 1
        if color > 9:
            color = 0
        return self.write({'state_color': str(color)})


class AssetCategory(models.Model):
    _description = 'Asset Tags'
    _name = 'asset.category'

    name = fields.Char('Tag', required=True, translate=True)
    asset_ids = fields.Many2many(comodel_name='asset.asset', column1='category_id', column2='asset_id', string='Assets')


class AssetAsset(models.Model):
    """
    Assets
    """
    _name = 'asset.asset'
    _description = 'Asset'
    _inherit = ['mail.thread', 'image.mixin']

    @api.model
    def _read_group_state_ids(self, states, domain, order):
        team = '3'
        stage_obj = self.env['asset.state']
        search_domain = []
        search_domain += ['|', ('team', '=', team)]
        search_domain += [('id', 'in', states.ids)]
        return stage_obj.search(search_domain, order=order)

    @api.model
    def _read_group_finance_state_ids(self, states, domain, order):
        team = '0'
        stage_obj = self.env['asset.state']
        search_domain = []
        search_domain += ['|', ('team', '=', team)]
        search_domain += [('id', 'in', states.ids)]
        return stage_obj.search(search_domain, order=order)

    @api.model
    def _read_group_warehouse_state_ids(self, states, domain, order):
        team = '1'
        stage_obj = self.env['asset.state']
        search_domain = []
        search_domain += ['|', ('team', '=', team)]
        search_domain += [('id', 'in', states.ids)]
        return stage_obj.search(search_domain, order=order)

    @api.model
    def _read_group_manufacture_state_ids(self, states, domain, order):
        team = '2'
        stage_obj = self.env['asset.state']
        search_domain = []
        search_domain += ['|', ('team', '=', team)]
        search_domain += [('id', 'in', states.ids)]
        return stage_obj.search(search_domain, order=order)

    @api.model
    def _read_group_maintenance_state_ids(self, states, domain, order):
        team = '3'
        stage_obj = self.env['asset.state']
        search_domain = []
        search_domain += ['|', ('team', '=', team)]
        search_domain += [('id', 'in', states.ids)]
        return stage_obj.search(search_domain, order=order)
        
    @api.model
    def _read_group_accounting_state_ids(self, states, domain, order):
        team = '4'
        stage_obj = self.env['asset.state']
        search_domain = []
        search_domain += ['|', ('team', '=', team)]
        search_domain += [('id', 'in', states.ids)]
        return stage_obj.search(search_domain, order=order)

    CRITICALITY_SELECTION = [
        ('0', 'General'),
        ('1', 'Important'),
        ('2', 'Very important'),
        ('3', 'Critical')
    ]

    name = fields.Char('Asset Name', size=64, required=True, translate=True)
    finance_state_id = fields.Many2one(comodel_name='asset.state', domain=[('team','=','0')])
    warehouse_state_id = fields.Many2one(comodel_name='asset.state', domain=[('team','=','1')])
    manufacture_state_id = fields.Many2one(comodel_name='asset.state', domain=[('team','=','2')])
    maintenance_state_id = fields.Many2one(comodel_name='asset.state', domain=[('team','=','3')])
    accounting_state_id = fields.Many2one(comodel_name='asset.state', domain=[('team','=','4')])
    maintenance_state_color = fields.Selection(
        related='maintenance_state_id.state_color', string="Maintenance state color", readonly=True
    )
    criticality = fields.Selection(selection=CRITICALITY_SELECTION, string='Criticality')
    property_stock_asset = fields.Many2one(
        comodel_name='stock.location', string="Asset Location",
        company_dependent=True, domain=[('usage', 'like', 'asset')],
        help="This location will be used as the destination location for installed parts during asset life.")
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned to', tracking=True)
    active = fields.Boolean(string='Active', default=True)
    asset_number = fields.Char(string='Asset Number', size=64)
    model = fields.Char(string='Model', size=64)
    serial = fields.Char(string='Serial no.', size=64)
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor')
    manufacturer_id = fields.Many2one(comodel_name='res.partner', string='Manufacturer')
    start_date = fields.Date(string='Start Date')
    purchase_date = fields.Date(string='Purchase Date')
    warranty_start_date = fields.Date(string='Warranty Start')
    warranty_end_date = fields.Date(string='Warranty End')
    category_ids = fields.Many2many(
        comodel_name='asset.category', column1='asset_id', column2='category_id', string='Tags'
    )

    _group_by = {
        'finance_state_id': _read_group_finance_state_ids,
        'warehouse_state_id': _read_group_warehouse_state_ids,
        'manufacture_state_id': _read_group_manufacture_state_ids,
        'maintenance_state_id': _read_group_maintenance_state_ids,
        'accounting_state_id': _read_group_accounting_state_ids,
    }

    @api.model
    def create(self, vals):
        # if 'image' in vals:
        #     vals['image_128'] = vals['image_512'] = vals['image']
        return super(AssetAsset, self).create(vals)

    def write(self, vals):
        # if 'image' in vals:
        #     vals['image_128'] = vals['image_512'] = vals['image']
        return super(AssetAsset, self).write(vals)

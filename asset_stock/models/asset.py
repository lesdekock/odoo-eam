# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2014-2016 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models
from odoo.addons.asset.models.asset import STATE_COLOR_SELECTION


class AssetAsset(models.Model):
    _inherit = 'asset.asset'

    warehouse_state_color = fields.Selection(related='warehouse_state_id.state_color', string="Color", readonly=True)

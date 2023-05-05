# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2018 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models
from odoo.addons.asset.models.asset import STATE_COLOR_SELECTION


class AssetAsset(models.Model):
    _inherit = 'asset.asset'

    accounting_state_color = fields.Selection(
        related='accounting_state_id.state_color', string="Accounting state color", readonly=True
    )

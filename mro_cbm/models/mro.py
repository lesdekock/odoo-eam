# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2015-2018 CodUP (<http://codup.com>).
#
##############################################################################

import time
import calendar
from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


# noinspection PyPep8Naming
class MroOrder(models.Model):
    _inherit = 'mro.order'

    # MAINTENANCE_TYPE_SELECTION = [
    #     ('bm', 'Breakdown'),
    #     ('cm', 'Corrective'),
    #     ('pm', 'Preventive'),
    #     ('cbm', 'Predictive')
    # ]

    maintenance_type = fields.Selection(
        selection_add=[('pm', 'Preventive'), ('cbm', 'Predictive')],
        ondelete={"pm": "cascade", "cbm": "cascade"},
    )

    def replan_cbm(self):
        rule_obj = self.env['mro.cbm.rule']
        asset_obj = self.env['asset.asset']
        ids = rule_obj.search([])
        for rule in ids:
            for asset in rule.category_id.asset_ids:
                for gauge in asset.gauge_ids:
                    if gauge.name != rule.parameter_id or gauge.state != 'reading': continue
                    self.planning_strategy_2(asset, gauge, rule)
        return True

    def planning_strategy_2(self, asset, gauge, rule):
        gauge_line_obj = self.env['mro.gauge.line']
        gauge_reads = gauge_line_obj.search([('gauge_id', '=', gauge.id)], limit=1, order='date desc')[0]
        if (rule.is_limit_min and rule.limit_min > gauge_reads.value) or (
                rule.is_limit_max and rule.limit_max < gauge_reads.value):
            task = rule.task_id
            order_ids = self.search(
                [('asset_id', '=', asset.id),
                 ('state', 'not in', ('draft', 'cancel')),
                 ('maintenance_type', '=', 'cbm'),
                 ('task_id', '=', task.id)],
                limit=1, order='date_execution desc')
            if len(order_ids) > 0:
                date = order_ids[0].date_execution.strftime(DATETIME_FORMAT)
                Do = 1.0 * calendar.timegm(time.strptime(date, "%Y-%m-%d %H:%M:%S"))
                Dg = 1.0 * calendar.timegm(time.strptime(gauge_reads.date.strftime(DATE_FORMAT), "%Y-%m-%d"))
                if Do > Dg:
                    return True
            order_ids = self.search(
                [('asset_id', '=', asset.id),
                 ('state', '=', 'draft'),
                 ('maintenance_type', '=', 'cbm'),
                 ('task_id', '=', task.id)],
                order='date_execution')
            Tp = fields.datetime.now()
            values = {'date_planned': Tp, 'date_scheduled': Tp, 'date_execution': Tp, 'origin': rule.name,
                      'state': 'draft', 'maintenance_type': 'cbm', 'asset_id': asset.id, 'task_id': task.id,
                      'description': task.name, 'tools_description': task.tools_description,
                      'labor_description': task.labor_description,
                      'operations_description': task.operations_description,
                      'documentation_description': task.documentation_description}
            parts_lines = []
            for line in task.parts_lines:
                parts_lines.append([0, 0, {
                    'name': line.name,
                    'part_id': line.part_id.id,
                    'part_uom_qty': line.part_uom_qty,
                    'part_uom': line.part_uom.id,
                }])
            if len(order_ids) > 0:
                order = order_ids[0]
                values['parts_lines'] = parts_lines + [[2, line.id] for line in order.parts_lines]
                order.write(values)
                return True
            values['parts_lines'] = parts_lines
            self.create(values)
        return True


class MroTask(models.Model):
    _inherit = 'mro.task'

    # MAINTENANCE_TYPE_SELECTION = [
    #     ('cm', 'Corrective'),
    #     ('pm', 'Preventive'),
    #     ('cbm', 'Predictive')
    # ]

    maintenance_type = fields.Selection(selection_add=[('cbm', 'Predictive')], ondelete={"cbm": "cascade"})

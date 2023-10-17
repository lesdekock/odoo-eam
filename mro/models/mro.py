# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2020 CodUP (<http://codup.com>).
#
##############################################################################

import time
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
# from odoo import netsvc
from odoo.addons.base.models import decimal_precision as dp


class MroOrder(models.Model):
    """
    Maintenance Orders
    """
    _name = 'mro.order'
    _description = 'Maintenance Order'
    _inherit = ['mail.thread']
    _order = 'date_execution'

    STATE_SELECTION = [
        ('draft', 'DRAFT'),
        ('released', 'WAITING PARTS'),
        ('ready', 'READY TO MAINTENANCE'),
        ('done', 'DONE'),
        ('cancel', 'CANCELED')
    ]

    # MAINTENANCE_TYPE_SELECTION = [
    #     ('bm', 'Breakdown'),
    #     ('cm', 'Corrective')
    # ]

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'ready':
            return self.env.ref('mro.mt_order_confirmed')
        return super(MroOrder, self)._track_subtype(init_values)

    def _get_available_parts(self):
        for order in self:
            line_ids = []
            available_line_ids = []
            done_line_ids = []

            if order.procurement_group_id:
                # In Odoo v14 and later, 'stock_move_ids' is used instead of 'move_ids'
                for move in order.procurement_group_id.stock_move_ids:
                    if move.location_dest_id.id == order.asset_id.property_stock_asset.id:
                        line_ids.append(move.id)
                        if move.state == 'assigned':
                            available_line_ids.append(move.id)
                        elif move.state == 'done':
                            done_line_ids.append(move.id)

            order.parts_ready_lines = order.parts_ready_lines.search([('id', 'in', line_ids)])
            order.parts_move_lines = order.parts_ready_lines.search([('id', 'in', available_line_ids)])
            order.parts_moved_lines = order.parts_ready_lines.search([('id', 'in', done_line_ids)])

    name = fields.Char('Reference')
    sequence = fields.Integer(string='Sequence', default=10)

    origin = fields.Char(
        'Source Document', size=64, readonly=True, states={'draft': [('readonly', False)]},
        help="Reference of the document that generated this maintenance order."
    )
    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
        help="When the maintenance order is created the status is set to 'Draft'.\n\
        If the order is confirmed the status is set to 'Waiting Parts'.\n\
        If the stock is available then the status is set to 'Ready to Maintenance'.\n\
        When the maintenance is over, the status is set to 'Done'.", default='draft')
    maintenance_type = fields.Selection(
        selection=[('bm', 'Breakdown'), ('cm', 'Corrective')], string='Maintenance Type', required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default='bm'
    )
    task_id = fields.Many2one('mro.task', 'Task', readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Char(
        'Description', translate=True, required=True, readonly=True, states={'draft': [('readonly', False)]}
    )
    asset_id = fields.Many2one(
        'asset.asset', 'Asset', required=True, readonly=True, states={'draft': [('readonly', False)]}
    )
    date_confirmed = fields.Datetime(
        string='Confirmed Date', required=True, readonly=True, index=True,
        states={'draft': [('readonly', False)], 'released': [('readonly', False)]}, copy=False,
        default=fields.Datetime.now, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders."
    )
    date_planned = fields.Datetime(
        'Planned Date', required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=time.strftime('%Y-%m-%d %H:%M:%S')
    )
    date_scheduled = fields.Datetime(
        'Scheduled Date', required=True, readonly=True, states={
            'draft': [('readonly', False)], 'released': [('readonly', False)], 'ready': [('readonly', False)]
        }, default=time.strftime('%Y-%m-%d %H:%M:%S')
    )
    date_execution = fields.Datetime('Execution Date', required=True, states={
        'done': [('readonly', True)], 'cancel': [('readonly', True)]
    }, default=time.strftime('%Y-%m-%d %H:%M:%S'))
    parts_lines = fields.One2many(
        'mro.order.parts.line', 'maintenance_id', 'Planned parts', readonly=True,
        states={'draft': [('readonly', False)], 'released': [('readonly', False)], 'ready': [('readonly', False)]}
    )
    parts_ready_lines = fields.One2many('stock.move', compute='_get_available_parts')
    parts_move_lines = fields.One2many('stock.move', compute='_get_available_parts')
    parts_moved_lines = fields.One2many('stock.move', compute='_get_available_parts')
    tools_description = fields.Text('Tools Description',translate=True)
    labor_description = fields.Text('Labor Description',translate=True)
    operations_description = fields.Text('Operations Description', translate=True)
    documentation_description = fields.Text('Documentation Description', translate=True)
    problem_description = fields.Text('Problem Description')
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self._uid)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('mro.order')
    )
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement group', copy=False)
    category_ids = fields.Many2many(related='asset_id.category_ids', string='Asset Category', readonly=True)
    wo_id = fields.Many2one('mro.workorder', 'Work Order', ondelete='cascade')
    request_id = fields.Many2one('mro.request', 'Request')
    # TODO: LDK Set initial execution date based on the following picking policy or create new date to represent
    #  forecasted date of product availability (picking_policy)
    picking_policy = fields.Selection(
        selection=[('direct', 'As soon as possible'), ('one', 'When all products are ready')],
        string='Picking Policy', required=True, readonly=True, default='direct',
        states={'draft': [('readonly', False)], 'released': [('readonly', False)]},
        help="If you pick all products at once, the maintenance order will be scheduled based on the greatest "
        "product lead time. Otherwise, it will be based on the shortest.")
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse', string='Workshop', required=True, readonly=True,
        states={'draft': [('readonly', False)]}, check_company=True
    )
    picking_ids = fields.One2many('stock.picking', 'maintenance_id', string='Transfers')

    @api.onchange('asset_id','maintenance_type')
    def onchange_asset(self):
        if self.asset_id:
            self.category_ids = self.asset_id.category_ids
        return {'domain': {'task_id': [('category_id', 'in', self.category_ids.ids),('maintenance_type','=',self.maintenance_type)]}}

    @api.onchange('date_planned')
    def onchange_planned_date(self):
        self.date_scheduled = self.date_planned

    @api.onchange('date_scheduled')
    def onchange_scheduled_date(self):
        self.date_execution = self.date_scheduled

    @api.onchange('date_execution')
    def onchange_execution_date(self):
        if self.state == 'draft':
            self.date_planned = self.date_execution
        else:
            self.date_scheduled = self.date_execution

    @api.onchange('task_id')
    def onchange_task(self):
        task = self.task_id
        new_parts_lines = []
        for line in task.parts_lines:
            new_parts_lines.append([0,0,{
                'name': line.name,
                'part_id': line.part_id.id,
                'part_uom_qty': line.part_uom_qty,
                'part_uom': line.part_uom.id,
                }])
        self.parts_lines = new_parts_lines
        self.description = task.name
        self.tools_description = task.tools_description
        self.labor_description = task.labor_description
        self.operations_description = task.operations_description
        self.documentation_description = task.documentation_description

    # TODO: CODUP -Test Logic of test_ready for new logic Note: Is seems as if the class procurement.order has been
    #  removed and logic directly incorporated into stock.move. To be verified!
    def test_ready(self):
        res = True
        for order in self:
            if order.parts_lines and order.procurement_group_id:
                states = []
                for stock_move in order.procurement_group_id.stock_move_ids:
                    if stock_move.location_dest_id.id == order.asset_id.property_stock_asset.id:
                        states += [stock_move.state != 'assigned']
                if any(states) or len(states) == 0:
                    res = False
        return res

    def _action_confirm(self):
        self.parts_lines._action_launch_stock_rule()
        return True

    @api.model
    def _get_forbidden_state_confirm(self):
        return {'done', 'cancel'}

    @api.model
    def _prepare_confirmation_values(self):
        return {
            'state': 'released',
            'date_confirmed': fields.Datetime.now()
        }

    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        self.write(self._prepare_confirmation_values())

        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        return True

    def action_ready(self):
        self.write({'state': 'ready'})
        return True

    def action_done(self):
        self.write({'state': 'done', 'date_execution': time.strftime('%Y-%m-%d %H:%M:%S')})
        for order in self:
            if order.request_id: order.request_id.action_done()
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def test_if_parts(self):
        res = True
        for order in self:
            if not order.parts_lines:
                res = False
        return res

    def force_done(self):
        self.write({'state': 'done', 'date_execution': time.strftime('%Y-%m-%d %H:%M:%S')})
        for order in self:
            if order.request_id: order.request_id.action_done()
        return True

    def force_parts_reservation(self):
        self.write({'state': 'ready'})
        return True

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('mro.order') or '/'
        return super(MroOrder, self).create(vals)

    def write(self, vals):
        if vals.get('date_execution') and not vals.get('state'):
            # constraint for calendar view
            for order in self:
                if order.state == 'draft':
                    vals['date_planned'] = vals['date_execution']
                    vals['date_scheduled'] = vals['date_execution']
                elif order.state in ('released','ready'):
                    vals['date_scheduled'] = vals['date_execution']
                else:
                    del vals['date_execution']
        res = super(MroOrder, self).write(vals)
        if 'parts_lines' in vals:
            self.parts_lines._action_launch_stock_rule()
        return res


# noinspection DuplicatedCode
class MroOrderPartsLine(models.Model):
    _name = 'mro.order.parts.line'
    _description = 'Maintenance Planned Parts'

    name = fields.Char(string='Description', size=64)
    sequence = fields.Integer(string='Sequence', default=10)
    maintenance_id = fields.Many2one(comodel_name='mro.order',  string='Maintenance Order')
    part_id = fields.Many2one(comodel_name='product.product', string='Parts', required=True)
    part_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    part_uom = fields.Many2one(
        comodel_name='uom.uom', string='Unit of Measure', required=True,
        domain="[('category_id', '=', part_uom_category_id)]", ondelete="restrict"
    )
    part_uom_category_id = fields.Many2one(related='part_id.uom_id.category_id')
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    company_id = fields.Many2one(related='maintenance_id.company_id', string='Company', store=True, index=True)
    state = fields.Selection(
        related='maintenance_id.state', string='Order Status', copy=False, store=True
    )

    move_ids = fields.One2many('stock.move', 'part_line_id', string='Stock Moves')

    @api.onchange('part_id')
    def onchange_parts(self):
        self.part_uom = self.part_id.uom_id

    def unlink(self):
        self.write({'maintenance_id': False})
        return True

    @api.model
    def create(self, values):
        ids = self.search([('maintenance_id', '=', values['maintenance_id']), ('part_id', '=', values['part_id'])])
        if len(ids)>0:
            values['part_uom_qty'] = ids[0].part_uom_qty + values['part_uom_qty']
            ids[0].write(values)
            return ids[0]
        ids = self.search([('maintenance_id', '=', False)])
        if len(ids)>0:
            ids[0].write(values)
            return ids[0]
        return super(MroOrderPartsLine, self).create(values)

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a maintenance order parts line. This method could be override in order to add other custom
        key that could be used in move/po creation.
        """
        values = {}
        self.ensure_one()
        # Use the delivery date if there is else use date_order and lead time
        date_deadline = self.maintenance_id.date_scheduled
        date_planned = self.maintenance_id.date_planned
        values.update({
            'group_id': group_id,
            'part_line_id': self.id,
            'date_planned': date_planned,
            'date_d1eadline': date_deadline,
            'route_ids': self.env.ref('mro.route_maintenance'),
            # **** CONTINUE HERE ********** consider warehouse_id is the workshop location and thus also it's
            # spares location ????'
            'warehouse_id': self.maintenance_id.warehouse_id or False,
            # 'partner_id': self.order_id.partner_shipping_id.id,
            # 'product_description_variants': self.with_context(lang=self.order_id.partner_id.lang)._get_sale_order_line_multiline_description_variants(),
            'company_id': self.maintenance_id.company_id,
            # 'product_packaging_id': self.product_packaging_id,
            'sequence': self.sequence,
        })
        return values

    def _get_qty_procurement(self, previous_part_uom_qty=False):
        self.ensure_one()
        qty = 0.0
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        for move in outgoing_moves:
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.part_uom, rounding_method='HALF-UP')
        for move in incoming_moves:
            qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.part_uom, rounding_method='HALF-UP')
        return qty

    def _get_outgoing_incoming_moves(self):
        outgoing_moves = self.env['stock.move']
        incoming_moves = self.env['stock.move']

        moves = self.move_ids.filtered(
            lambda r: r.state != 'cancel' and not r.scrapped and self.part_id == r.product_id
        )
        if self._context.get('accrual_entry_date'):
            moves = moves.filtered(
                lambda r: fields.Date.context_today(r, r.date) <= self._context['accrual_entry_date']
            )

        for move in moves:
            if move.location_dest_id.usage == "asset":
                if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                    outgoing_moves |= move
            elif move.location_dest_id.usage != "asset" and move.to_refund:
                incoming_moves |= move

        return outgoing_moves, incoming_moves

    def _get_procurement_group(self):
        return self.maintenance_id.procurement_group_id

    def _prepare_procurement_group_vals(self):
        return {
            'name': self.maintenance_id.name,
            'move_type': self.maintenance_id.picking_policy,
            'maintenance_id': self.maintenance_id.id,
            # TODO: LDK MRO Review if needed (partner_id) on procurement group
            # 'partner_id': self.maintenance_id.partner_shipping_id.id,
        }

    def _action_launch_stock_rule(self, previous_part_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        if self._context.get("skip_procurement"):
            return True
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'released' or not line.part_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_part_uom_qty)
            if float_compare(qty, line.part_uom_qty, precision_digits=precision) == 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.maintenance_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                # TODO: LDK MRO Review if needed (partner_id) on procurement group
                # if group_id.partner_id != line.order_id.partner_shipping_id:
                #     updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.maintenance_id.picking_policy:
                    updated_vals.update({'move_type': line.maintenance_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            part_qty = line.part_uom_qty - qty

            line_uom = line.part_uom
            quant_uom = line.part_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(part_qty, quant_uom)
            procurements.append(self.env['procurement.group'].Procurement(
                line.part_id, product_qty, procurement_uom,
                line.maintenance_id.asset_id.property_stock_asset,
                line.part_id.display_name, line.maintenance_id.name, line.maintenance_id.company_id, values))
        if procurements:
            procurement_group = self.env['procurement.group']
            if self.env.context.get('import_file'):
                procurement_group = procurement_group.with_context(import_file=False)
            procurement_group.run(procurements)

        # This next block is currently needed only because the scheduler trigger is done by picking confirmation rather than stock.move confirmation
        orders = self.mapped('maintenance_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])
            if pickings_to_confirm:
                # Trigger the Scheduler for Pickings
                pickings_to_confirm.action_confirm()
        return True

    @api.onchange('part_uom', 'part_uom_qty')
    def product_uom_change(self):
        if not self.part_uom or not self.part_id:
            self.price_unit = 0.0
        else:
            self.price_unit = self.part_id.standard_price


class MroTask(models.Model):
    """
    Maintenance Tasks (Template for order)
    """
    _name = 'mro.task'
    _description = 'Maintenance Task'

    # MAINTENANCE_TYPE_SELECTION = [
    #     ('cm', 'Corrective')
    # ]

    name = fields.Char('Description', size=64, required=True, translate=True)
    category_id = fields.Many2one('asset.category', 'Asset Category', ondelete='restrict', required=True)
    maintenance_type = fields.Selection(
        selection=[('cm', 'Corrective')], string='Maintenance Type', required=True, default='cm'
    )
    parts_lines = fields.One2many('mro.task.parts.line', 'task_id', 'Parts')
    tools_description = fields.Text('Tools Description',translate=True)
    labor_description = fields.Text('Labor Description',translate=True)
    operations_description = fields.Text('Operations Description',translate=True)
    documentation_description = fields.Text('Documentation Description',translate=True)
    active = fields.Boolean('Active', default=True)


class MroTaskPartsLine(models.Model):
    _name = 'mro.task.parts.line'
    _description = 'Maintenance Planned Parts'

    name = fields.Char('Description', size=64)
    part_id = fields.Many2one('product.product', 'Parts', required=True)
    part_uom_qty = fields.Float('Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    part_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    task_id = fields.Many2one('mro.task', 'Maintenance Task')

    @api.onchange('part_id')
    def onchange_parts(self):
        self.part_uom = self.part_id.uom_id.id

    def unlink(self):
        self.write({'task_id': False})
        return True

    @api.model
    def create(self, values):
        ids = self.search([('task_id','=',values['task_id']),('part_id','=',values['part_id'])])
        if len(ids)>0:
            values['part_uom_qty'] = ids[0].part_uom_qty + values['part_uom_qty']
            ids[0].write(values)
            return ids[0]
        ids = self.search([('task_id','=',False)])
        if len(ids)>0:
            ids[0].write(values)
            return ids[0]
        return super(MroTaskPartsLine, self).create(values)


class MroRequest(models.Model):
    _name = 'mro.request'
    _description = 'Maintenance Request'
    _inherit = ['mail.thread']

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('claim', 'Claim'),
        ('run', 'Execution'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled')
    ]

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'claim':
            return self.env.ref('mro.mt_request_sent')
        elif 'state' in init_values and self.state == 'run':
            return self.env.ref('mro.mt_request_confirmed')
        elif 'state' in init_values and self.state == 'reject':
            return self.env.ref('mro.mt_request_rejected')
        return super(MroRequest, self)._track_subtype(init_values)

    name = fields.Char('Reference', size=64)
    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
        help="When the maintenance request is created the status is set to 'Draft'.\n\
        If the request is sent the status is set to 'Claim'.\n\
        If the request is confirmed the status is set to 'Execution'.\n\
        If the request is rejected the status is set to 'Rejected'.\n\
        When the maintenance is over, the status is set to 'Done'.", tracking=True, default='draft')
    asset_id = fields.Many2one('asset.asset', 'Asset', required=True, readonly=True, states={'draft': [('readonly', False)]})
    cause = fields.Char('Cause', size=64, translate=True, required=True, readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text('Description', readonly=True, states={'draft': [('readonly', False)]})
    reject_reason = fields.Text('Reject Reason', readonly=True)
    requested_date = fields.Datetime('Requested Date', required=True, readonly=True, states={'draft': [('readonly', False)]}, help="Date requested by the customer for maintenance.", default=time.strftime('%Y-%m-%d %H:%M:%S'))
    execution_date = fields.Datetime('Execution Date', required=True, readonly=True, states={'draft':[('readonly',False)],'claim':[('readonly',False)]}, default=time.strftime('%Y-%m-%d %H:%M:%S'))
    breakdown = fields.Boolean('Breakdown', readonly=True, states={'draft': [('readonly', False)]}, default=False)
    create_uid = fields.Many2one('res.users', 'Responsible')

    @api.onchange('requested_date')
    def onchange_requested_date(self):
        self.execution_date = self.requested_date

    @api.onchange('execution_date', 'state', 'breakdown')
    def onchange_execution_date(self):
        if self.state == 'draft' and not self.breakdown:
            self.requested_date = self.execution_date

    def action_send(self):
        value = {'state': 'claim'}
        for request in self:
            if request.breakdown:
                value['requested_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
            request.write(value)

    def action_confirm(self):
        order = self.env['mro.order']
        for request in self:
            order.create({
                'date_planned': request.requested_date,
                'date_scheduled': request.requested_date,
                'date_execution': request.requested_date,
                'origin': request.name,
                'state': 'draft',
                'maintenance_type': 'bm',
                'asset_id': request.asset_id.id,
                'description': request.cause,
                'problem_description': request.description,
                'request_id': request.id,
            })
        self.write({'state': 'run'})

    def action_done(self):
        self.write({'state': 'done', 'execution_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    def action_reject(self):
        self.write({'state': 'reject', 'execution_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    def action_cancel(self):
        self.write({'state': 'cancel', 'execution_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    @api.model
    def create(self, vals):
        if vals.get('name','/')=='/':
            vals['name'] = self.env['ir.sequence'].next_by_code('mro.request') or '/'
        return super(MroRequest, self).create(vals)

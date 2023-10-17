# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2014-2018 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models
from odoo.tools.sql import column_exists, create_column


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    maintenance_id = fields.Many2one(
        related="group_id.maintenance_id", string="Maintenance Order", store=True, readonly=False
    )
    
    def _auto_init(self):
        """
        Create related field here, too slow
        when computing it afterwards through _compute_related.

        Since group_id.sale_id is created in this module,
        no need for an UPDATE statement.
        """
        if not column_exists(self.env.cr, 'stock_picking', 'maintenance_id'):
            create_column(self.env.cr, 'stock_picking', 'maintenance_id', 'int4')
        return super()._auto_init()

    def _action_done(self):
        res = super()._action_done()
        maintenance_order_lines_vals = []
        for move in self.move_lines:
            maintenance_order = move.picking_id.maintenance_id
            # Creates new  Parts line only when pickings linked to a maintenance order and
            # for moves with qty. done and not already linked to a maintenance order line.
            if (not maintenance_order or move.location_dest_id.usage != 'asset' or move.part_line_id or
                    not move.quantity_done):
                continue
            product = move.product_id
            mo_line_vals = {
                'move_ids': [(4, move.id, 0)],
                'name': product.display_name,
                'maintenance_id': maintenance_order.id,
                'part_id': product.id,
                'part_uom_qty': 0,
                # 'qty_delivered': move.quantity_done,
                'part_uom': move.product_uom.id,
                'price_unit': product.standard_price,
            }
            # if product.invoice_policy == 'delivery':
            #     # Check if there is already a SO line for this product to get
            #     # back its unit price (in case it was manually updated).
            #     mo_line = maintenance_order.parts_lines.filtered(lambda mol: mol.part_id == product)
            #     if mo_line:
            #         mo_line_vals['price_unit'] = mo_line[0].price_unit
            # elif product.invoice_policy == 'order':
            #     # No unit price if the product is invoiced on the ordered qty.
            #     mo_line_vals['price_unit'] = 0
            maintenance_order_lines_vals.append(mo_line_vals)

        if maintenance_order_lines_vals:
            self.env['mro.order.parts.line'].with_context(skip_procurement=True).create(maintenance_order_lines_vals)
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    part_line_id = fields.Many2one('mro.order.parts.line', 'MRO Parts Line', index=True)

    # @api.model
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        # from odoo import workflow
        if vals.get('state') == 'assigned':
            mro_obj = self.env['mro.order']
            order_ids = mro_obj.search([('procurement_group_id', 'in', [x.group_id.id for x in self])])
            for order_id in order_ids:
                if order_id.test_ready():
                    # workflow.trg_validate(self.env.user.id, 'mro.order', order_id.id, 'parts_ready', self.env.cr)
                    order_id.action_ready()
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    maintenance_id = fields.Many2one('mro.order', 'Maintenance Order')

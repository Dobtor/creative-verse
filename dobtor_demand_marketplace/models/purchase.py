# -*- coding: utf-8 -*-
import logging
import pprint
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    transaction_ids = fields.Many2many(
        'payment.transaction', 'purchase_order_transaction_rel', 'purchase_id', 'transaction_id', 
        string='Transactions', copy=False, readonly=True)

    def demand_action_create_purchase_transaction(self):
        for po in self.filtered(lambda l: l.partner_id and l.state in ["purchase"]):
            acquirer = self.env["payment.acquirer"].sudo().get_wallet_acquirer()
            tx_obj = self.env['payment.transaction'].sudo()
            tx_vals = tx_obj.prepare_wallet_tx_val(
                acquirer,
                po.amount_total,
                po.partner_id.id,
                source=po.name
            )
            tx = tx_obj.create(tx_vals)
            if tx:
                tx.update({
                    "purchase_ids": [(6, 0, [po.id])],
                    "waiting_for_invoice": False
                })
                tx._set_transaction_done()
                po.update({"transaction_ids": [(6, 0, [tx.id])]})
                tx.demand_generate_and_appropriate_wallet_invoice(po)
# -*- coding: utf-8 -*-
from email.policy import default
from odoo import api, fields, models, _
import pprint
import logging
import re
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_agent_payment = fields.Boolean(
        string='Agent Paying',
        help='agent for the collecting and paying',
        default=False
    )

    def set_agent_payment(self):
        for res in self:
            res.is_agent_payment = True

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        for order in self:
            if order.is_agent_payment == True:
                for move in moves:
                    if order.name in re.sub(r"\s+", "", move.invoice_origin).split(','):
                        move.is_agent_payment = True
        return moves

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    request_qty = fields.Integer(
        string='Request Qty',
        default=1,
    )

    def _get_display_price(self, product):
        if self.request_qty:
            return super()._get_display_price(product) * self.request_qty
    
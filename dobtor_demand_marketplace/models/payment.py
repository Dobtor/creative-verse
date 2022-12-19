# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    event_register = fields.Many2one(
        string='Event Registration',
        comodel_name='event.registration',
        ondelete='set null',
    )
    purchase_ids = fields.Many2many(
        'purchase.order',
        'purchase_order_transaction_rel',
        'transaction_id', 'purchase_id',
        string='Purchase Orders',
        copy=False,
        readonly=True
    )

    def demand_create_purchase_payment(self, add_payment_vals={}):
        self.ensure_one()
        payment_vals = {
            'amount': self.amount,
            'payment_type': 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': 'supplier',
            'journal_id': self.acquirer_id.journal_id.id,
            'company_id': self.acquirer_id.company_id.id,
            'payment_method_id': self.env.ref('payment.account_payment_method_electronic_in').id,
            'payment_token_id': self.payment_token_id and self.payment_token_id.id or None,
            'payment_transaction_id': self.id,
            'ref': self.reference,
            **add_payment_vals,}
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()

        self.payment_id = payment
        if self.invoice_ids:
            self.invoice_ids.filtered(lambda move: move.state == 'draft')._post()

        (payment.line_ids + self.invoice_ids.line_ids)\
        .filtered(lambda line: line.account_id == payment.destination_account_id and not line.reconciled)\
        .reconcile()

        self._set_transaction_done()
        self.write({
            "is_processed": True,
            "waiting_for_invoice": False
        })

    def demand_generate_and_appropriate_wallet_invoice(self, order, add_payment_vals={}):
        self.ensure_one()
        order.action_create_invoice()
        created_invoice = order.invoice_ids
        if created_invoice:
            created_invoice.write({"invoice_date": fields.Date.context_today(self)})
            self.invoice_ids = [(6, 0, created_invoice.ids)]
            self.demand_create_purchase_payment()
            # 代收代付不用 建立 Market Entry
            # self._create_wallet_bill_entry()


    def _prepare_invoice_values(self, order, name, amount, so_line):
        move_val = super()._prepare_invoice_values(order, name, amount, so_line)
        if order.is_agent_payment == True:
            move_val.update({
                'is_agent_payment': True
            })
        return move_val
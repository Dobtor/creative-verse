# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_invoice_paid(self):
        res = super().action_invoice_paid()
        self.mapped('line_ids.purchase_line_id')._update_registrations(confirm=True, mark_as_paid=True)
        return res

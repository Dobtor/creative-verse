# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import pprint
from odoo.exceptions import ValidationError, Warning, UserError
import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    is_agent_payment = fields.Boolean(
        string='Agent Paying',
        help='agent for the collecting and paying',
        default=False
    )

    def create_entry_constraint(self):
        if self.is_agent_payment:
            return False
        return super().create_entry_constraint()
        
            
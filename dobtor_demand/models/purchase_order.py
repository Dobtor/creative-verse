# -*- coding: utf-8 -*-
import logging
import pprint
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    demand_attendee_count = fields.Integer('Demand Attendee Count', compute='_compute_demand_attendee_count')

    def write(self, vals):
        result = super().write(vals)
        if vals.get('partner_id'):
            registrations_toupdate = self.env['event.registration'].search([('demand_po_id', 'in', self.ids)])
            registrations_toupdate.write({'partner_id': vals['partner_id']})
        return result

    def button_confirm(self):
        res = super().button_confirm()
        for po in self:
            po.order_line._update_registrations(confirm=po.amount_total == 0, cancel_to_draft=False)
            if any(line.event_id for line in po.order_line):
                return self.env['ir.actions.act_window'] \
                    .with_context(default_demand_po_id=po.id) \
                    ._for_xml_id('dobtor_demand.action_purchase_order_event_registration')
        return res

    def action_view_attendee_list(self):
        action = self.env["ir.actions.actions"]._for_xml_id("event.event_registration_action_tree")
        action['domain'] = [('demand_po_id', 'in', self.ids)]
        return action

    def _compute_demand_attendee_count(self):
        purchase_orders_data = self.env['event.registration'].read_group(
            [('demand_po_id', 'in', self.ids)],
            ['demand_po_id'], ['demand_po_id']
        )
        attendee_count_data = {
            purchase_order_data['demand_po_id'][0]:
            purchase_order_data['demand_po_id_count']
            for purchase_order_data in purchase_orders_data
        }
        for purchase_order in self:
            purchase_order.demand_attendee_count = attendee_count_data.get(purchase_order.id, 0)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    event_id = fields.Many2one(
        'event.event',
        string='Event',
        help="Choose an event and it will automatically create a registration for this event.")
    event_ticket_id = fields.Many2one(
        'event.event.ticket',
        string='Event Ticket',
        help="Choose an event ticket and it will automatically create a registration for this event ticket.")
    event_ok = fields.Boolean(
        related='product_id.event_ok', 
        readonly=True)
    request_qty = fields.Integer(
        string='Request Qty',
        default=1,
    )

    def _update_registrations(self, confirm=True, cancel_to_draft=False, registration_data=None, mark_as_paid=False):
        RegistrationSudo = self.env['event.registration'].sudo()
        registrations = RegistrationSudo.search([('demand_po_line_id', 'in', self.ids)])
        registrations_vals = []
        for po_line in self.filtered('event_id'):
            existing_registrations = registrations.filtered(lambda self: self.demand_po_line_id.id == po_line.id)
            if confirm:
                existing_registrations.filtered(lambda self: self.state not in ['open', 'cancel']).action_confirm()
            if mark_as_paid:
                existing_registrations.filtered(lambda self: not self.is_paid)._action_set_paid()
            if cancel_to_draft:
                existing_registrations.filtered(lambda self: self.state == 'cancel').action_set_draft()

            for count in range(int(po_line.product_qty) - len(existing_registrations)):
                values = {
                    'demand_po_line_id': po_line.id,
                    'demand_po_id': po_line.order_id.id
                }
                if registration_data:
                    values.update(registration_data.pop())
                registrations_vals.append(values)

        if registrations_vals:
            RegistrationSudo.create(registrations_vals)
        return True

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.event_id and (not self.product_id or self.product_id.id not in self.event_id.mapped('event_ticket_ids.product_id.id')):
            self.event_id = None

    @api.onchange('event_id')
    def _onchange_event_id(self):
        if self.event_ticket_id and (not self.event_id or self.event_id != self.event_ticket_id.event_id):
            self.event_ticket_id = None

    @api.onchange('product_uom', 'product_qty')
    def _onchange_quantity(self):
        if not self.event_ticket_id:
            super()._onchange_quantity()
        else:
            self.price_unit = self._get_display_price(self.product_id)

    @api.onchange('event_ticket_id')
    def _onchange_event_ticket_id(self):
        self._product_id_change()
        self._onchange_quantity()

    @api.onchange('request_qty')
    def _onchange_request_qty(self):
        self._onchange_quantity()

    def _get_product_purchase_description(self, product):
        if self.event_ticket_id:
            ticket = self.event_ticket_id.with_context(
                lang=self.order_id.partner_id.lang,
            )

            return ticket._get_ticket_multiline_purchase_description()
        else:
            return super()._get_product_purchase_description(product)

    def _get_display_price(self, product):
        # TODO : 需處理稅內價
        if self.event_ticket_id and self.event_id:
            company = self.event_id.company_id or self.env.company
            currency = company.currency_id
            return currency._convert(
                self.event_ticket_id.price * self.request_qty, self.order_id.currency_id,
                self.order_id.company_id or self.env.company.id,
                self.order_id.date_order or fields.Date.today())

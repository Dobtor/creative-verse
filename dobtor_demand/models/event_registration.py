# -*- coding: utf-8 -*-
import logging
from odoo.tools import float_is_zero
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    demand_po_id = fields.Many2one(
        'purchase.order', 
        string='Demand Purchase Order', 
        ondelete='set null',
        copy=False
    )
    demand_po_line_id = fields.Many2one(
        'purchase.order.line',
        string='Demand Purchase Order Line',
        ondelete='set null', 
        copy=False
    )
    request_qty = fields.Integer(
        string='Request Qty',
        default=1,
    )

    request_total_amount = fields.Float(
        string='Request Total Amount',
        compute='_compute_request_amount',
        store=True
    )

    @api.depends('request_qty', 'event_ticket_id.price')
    def _compute_request_amount(self):
        for attendee in self:
            if attendee.request_qty > 0:
                attendee.request_total_amount = attendee.request_qty * attendee.event_ticket_id.price


    @api.depends('is_paid', 'sale_order_id.currency_id', 'sale_order_line_id.price_total', 'demand_po_id','demand_po_id.currency_id', 'demand_po_line_id.price_total')
    def _compute_payment_status(self):
        for record in self:
            so = record.sale_order_id
            if len(so) > 0:
                 super()._compute_payment_status()
            else:
                po = record.demand_po_id
                po_line = record.demand_po_line_id
                if not po or float_is_zero(po_line.price_total, precision_digits=po.currency_id.rounding):
                    record.payment_status = 'free'
                elif record.is_paid:
                    record.payment_status = 'paid'
                else:
                    record.payment_status = 'to_pay'
    

    def action_view_purchase_order(self):
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.action_rfq_form")
        action['views'] = [(False, 'form')]
        action['res_id'] = self.demand_po_id.id
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('demand_po_line_id'):
                po_line_vals = self._synchronize_po_line_values(
                    self.env['purchase.order.line'].browse(vals['demand_po_line_id'])
                )
                vals.update(po_line_vals)
        registrations = super().create(vals_list)
        for registration in registrations:
            if registration.demand_po_id:
                registration.message_post_with_view(
                    'mail.message_origin_link',
                    values={'self': registration, 'origin': registration.demand_po_id},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return registrations

    def write(self, vals):
        if vals.get('demand_po_line_id'):
            po_line_vals = self._synchronize_po_line_values(
                self.env['purchase.order.line'].browse(vals['demand_po_line_id'])
            )
            vals.update(po_line_vals)

        if vals.get('event_ticket_id'):
            self.filtered(
                lambda registration: registration.event_ticket_id and registration.event_ticket_id.id != vals['event_ticket_id']
            )._purchase_order_ticket_type_change_notify(self.env['event.event.ticket'].browse(vals['event_ticket_id']))

        return super(EventRegistration, self).write(vals)

    def _synchronize_po_line_values(self, po_line):
        if po_line:
            return {
                'partner_id': po_line.order_id.partner_id.id,
                'event_id': po_line.event_id.id,
                'event_ticket_id': po_line.event_ticket_id.id,
                'demand_po_id': po_line.order_id.id,
                'demand_po_line_id': po_line.id,
            }
        return {}

    def _purchase_order_ticket_type_change_notify(self, new_event_ticket):
        fallback_user_id = self.env.user.id if not self.env.user._is_public() else self.env.ref("base.user_admin").id
        for registration in self:
            render_context = {
                'registration': registration,
                'old_ticket_name': registration.event_ticket_id.name,
                'new_ticket_name': new_event_ticket.name
            }
            user_id = registration.event_id.event_creator.id or registration.demand_po_id.user_id.id or fallback_user_id
            registration.demand_po_id._activity_schedule_with_view(
                'mail.mail_activity_data_warning',
                user_id=user_id,
                views_or_xmlid='event_sale.event_ticket_id_change_exception',
                render_context=render_context)
# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DemandRegistrationEditor(models.TransientModel):
    _name = "demand.registration.editor"
    _description = 'Edit Attendee Details on Demand Confirmation'

    demand_po_id = fields.Many2one('purchase.order', 'Purchase Order', required=True)
    event_registration_ids = fields.One2many('demand.registration.editor.line', 'editor_id', string='Registrations to Edit')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if not res.get('demand_po_id'):
            demand_po_id = res.get('demand_po_id', self._context.get('active_id'))
            res['demand_po_id'] = demand_po_id
        po = self.env['purchase.order'].browse(res.get('demand_po_id'))
        registrations = self.env['event.registration'].search([
            ('demand_po_id', '=', po.id),
            ('event_ticket_id', 'in', po.mapped('order_line.event_ticket_id').ids),
            ('state', '!=', 'cancel')])

        attendee_list = []
        for po_line in [l for l in po.order_line if l.event_ticket_id]:
            existing_registrations = [r for r in registrations if r.event_ticket_id == po_line.event_ticket_id]
            for reg in existing_registrations:
                attendee_list.append([0, 0, {
                    'event_id': reg.event_id.id,
                    'event_ticket_id': reg.event_ticket_id.id,
                    'registration_id': reg.id,
                    'name': reg.name,
                    'email': reg.email,
                    'phone': reg.phone,
                    'mobile': reg.mobile,
                    'po_order_line_id': po_line.id,
                }])
            for count in range(int(po_line.product_qty) - len(existing_registrations)):
                attendee_list.append([0, 0, {
                    'event_id': po_line.event_id.id,
                    'event_ticket_id': po_line.event_ticket_id.id,
                    'po_order_line_id': po_line.id,
                    'name': po_line.partner_id.name,
                    'email': po_line.partner_id.email,
                    'phone': po_line.partner_id.phone,
                    'mobile': po_line.partner_id.mobile,
                }])
        res['event_registration_ids'] = attendee_list
        res = self._convert_to_write(res)
        return res

    def action_make_registration(self):
        self.ensure_one()
        registrations_to_create = []
        for registration_line in self.event_registration_ids:
            values = registration_line.get_registration_data()
            if registration_line.registration_id:
                registration_line.registration_id.write(values)
            else:
                registrations_to_create.append(values)

        self.env['event.registration'].create(registrations_to_create)
        self.demand_po_id.order_line._update_registrations(confirm=self.demand_po_id.amount_total == 0)

        return {'type': 'ir.actions.act_window_close'}


class RegistrationEditorLine(models.TransientModel):
    """Event Registration"""
    _name = "demand.registration.editor.line"
    _description = 'Edit Attendee Line on Demand Confirmation'
    _order = "id desc"

    editor_id = fields.Many2one('demand.registration.editor')
    po_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')
    event_id = fields.Many2one('event.event', string='Event', required=True)
    registration_id = fields.Many2one('event.registration', 'Original Registration')
    event_ticket_id = fields.Many2one('event.event.ticket', string='Event Ticket')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    name = fields.Char(string='Name', index=True)

    def get_registration_data(self):
        self.ensure_one()
        return {
            'event_id': self.event_id.id,
            'event_ticket_id': self.event_ticket_id.id,
            'partner_id': self.editor_id.demand_po_id.partner_id.id,
            'name': self.name or self.editor_id.demand_po_id.partner_id.name,
            'phone': self.phone or self.editor_id.demand_po_id.partner_id.phone,
            'mobile': self.mobile or self.editor_id.demand_po_id.partner_id.mobile,
            'email': self.email or self.editor_id.demand_po_id.partner_id.email,
            'demand_po_id': self.editor_id.demand_po_id.id,
            'demand_po_line_id': self.po_order_line_id.id,
            'request_qty': self.po_order_line_id.request_qty
        }

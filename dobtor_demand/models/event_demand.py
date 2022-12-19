# -*- coding: utf-8 -*-
import logging
import pprint
from odoo.addons.http_routing.models.ir_http import slug
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class EventDemand(models.Model):
    _name = 'event.demand'
    _inherits = {'event.event': 'event_id'}
    _inherit = ['event.master.mixin', 'mail.thread', 'mail.activity.mixin', 'abstract.state']
    _description = 'Demand'
    _order = "date_begin desc, name desc"

    @api.model
    def index_state(self):
        return [
            (10, 'draft'),
            (20, 'open'),
            (30, 'cancel'),
            (40, 'closed'),
            (50, 'give_up'),
        ]

    @api.model
    def _state_selection(self):
        return [
            ('draft', _('Appeal')),
            ('open', _('Confirm')),
            ('cancel',_('Reject')),
            ('closed', _('Closed')),
            ('give_up', _('Cancel'))
        ]

    event_id = fields.Many2one(
        comodel_name='event.event',
        string='Event',
        required=True,
        readonly=True,
        ondelete='cascade',
        check_company=True
    )
    minion_ids = fields.One2many(
        string='Demand Schedule',
        comodel_name='event.demand.schedule',
        inverse_name='master_id'
    )
    is_finished = fields.Boolean(
        'Has the demand create so processed',
         default=False
    )
    

    def open_website_url(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.website_url,
            'target': 'self',
        }

    def action_demand_open_attendee(self):
        context = dict(self.env.context or {})
        context.update({
            'default_event_id': self.event_id.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'event.registration',
            'name': 'Attendees',
            'view_mode': 'kanban,tree,form,calendar,graph',
            'domain': [('event_id', '=', self.event_id.id)],
            'context': context,
            'help': _('''<p class="o_view_nocontent_smiling_face">
                    Create an Attendee
                </p>'''),
        }

    # region : implement state function
    def _set_state_template_pattern(self, constraint=(), state=False):
        super()._set_state_template_pattern(constraint, state)
        if not isinstance(self.id, models.NewId):
            self._sent_state_mail()

    def _get_email_to(self):
        return self.organizer_id.email or self.env.company.partner_id.email

    def _sent_state_mail(self):
        if isinstance(self.id, models.NewId) and self._origin.id:
            self = self._origin
        for record in self:
            template = self.env.ref(f'dobtor_demand.demand_notify_mail', raise_if_not_found=False)
            if template:
                subject = {
                    'draft': _('Your Create Demand') + f" [{record.name}]",
                    'open' : _('Demand was confirmed') + f" [{record.name}]",
                    'cancel': _('Demand was cancelled') + f" [{record.name}]",
                }.get(record.state, '')
                body = {
                    'draft': _('Your Create Deam, Please wait for agree.'),
                    'open': _('Your demand was confirmed and published.'),
                    'cancel': _('Thank you for this appeal, but I may have to say no this time.')
                }.get(record.state, '')
                if self._context.get('force_sent_mail', True) and record._get_email_to() and record.event_creator_partner.email and self.env.company.email and subject and body:
                    email_values = {
                        'email_to': record._get_email_to(), 
                        'email_from': self.env.company.email,
                        'subject': subject}
                    template.sudo().with_context(body=body).send_mail(record.id, email_values=email_values, force_send=True, raise_exception=False)

    @api.model
    def _set_state_open_extend(self):
        return {
            'is_published' : True
        }

    @api.model
    def _set_state_draft_extend(self):
        return {
            'is_published' : False
        }
    
    @api.model
    def _set_state_cancel_extend(self):
        return {
            'is_published': False
        }

    @api.model
    def _set_state_give_up_extend(self):
        return {
            'is_published': False
        }

    def _set_state_draft(self):
        """ Move the record to the draft state."""
        constraint = ('open', 'cancel', 'closed', 'give_up')
        self._set_state_template_pattern(constraint=constraint, state="draft")

    def _set_state_open(self):
        """ Move the record to the open state."""
        constraint = ('draft',)
        self._set_state_template_pattern(constraint=constraint, state="open")

    def _set_state_cancel(self):
        """ Move the record to the cancel state."""
        constraint = ('draft',)
        self._set_state_template_pattern(constraint=constraint, state="cancel")
    
    def _set_state_closed(self):
        """ Move the record to the closed state."""
        constraint = ('open',)
        self._set_state_template_pattern(constraint=constraint, state="closed")

    def _set_state_give_up(self):
        """ Move the record to the give_up state."""
        constraint = ('draft',)
        self._set_state_template_pattern(constraint=constraint, state="give_up")

    def set_state_closed(self, post={}):
        self._set_state_closed()

    def set_state_give_up(self, post={}):
        self._set_state_give_up()
    # endregion
    
    @api.model_create_multi
    def create(self, vals_list):
        demands = super().create(vals_list)
        for i, demand in enumerate(demands):
            to_write = {
                'mode': 'demand',
                'is_processed': True,
            }
            for k, v in vals_list[i].items():
                if k in self._fields and self._fields[k].store and k in demand.event_id._fields and demand.event_id._fields[k].store:
                    to_write[k] = v
            demand.event_id.write(to_write)
            demand._sent_state_mail()
        return demands

    def action_view_linked_orders(self):
        """ Redirects to the orders linked to the current events """
        sale_order_action = self.env["ir.actions.actions"]._for_xml_id(
            "sale.action_orders")
        sale_order_action.update({
            'domain': [('state', '!=', 'cancel'), ('order_line.event_id', 'in', self.ids)],
            'context': {'create': 0},
        })
        return sale_order_action

    def actoin_finish_all(self):
        for demand in self:
            for po in demand.event_id.registration_ids.filtered(lambda x: x.state in ('draft')).mapped("demand_po_id"):
                _logger.info(po)
                po.button_confirm()
                po.action_create_invoice()

    def _cron_process_demand_finish(self):
        demands = self.env['event.demand'].search([
            ('date_end', '<', fields.Datetime.now()),
            ('demand_type', '=', 'taker'),
            ('is_finished', '=', False)])
        for demand in demands:
            for po in demand.event_id.registration_ids.filtered(lambda x: x.state in ('draft')).mapped("demand_po_id"):
                po.button_confirm()
                po.action_create_invoice()
            demand.write({'is_finished': True})

    def unlink(self):
        for demands in self:
            demands.event_id.registration_ids.unlink()
            demands.event_id.unlink()
        super().unlink()


class EventDemandSchedule(models.Model):
    _name = "event.demand.schedule"
    _inherit = "event.minion.mixin"
    _description = "Demand Schedule"

    master_id = fields.Many2one(
        string='Demand',
        comodel_name='event.demand',
    )
    event_id = fields.Many2one(
        string='Event',
        related='master_id.event_id',
    )

    event_ticket_id = fields.Many2one(
        string='Pricing',
        comodel_name='event.event.ticket',
        ondelete='set null'
    )
    pricing_method = fields.Selection(
        string='Type',
        related='event_ticket_id.pricing_method',
        readonly=True
    )
    manpower = fields.Integer(
        string='Manpower',
    )
    amount = fields.Float(
        string='Amount',
        compute='_compute_cost_or_revenue'
    )
    
    @api.depends('manpower', 'event_ticket_id.price', 'hour_to', 'hour_from')
    def _compute_cost_or_revenue(self):
        for record in self:
            weight = 0
            if record.pricing_method == "times":
                weight = 1
            elif record.pricing_method == "per_hour":
                weight = (record.hour_to - record.hour_from) 
            record.amount = record.manpower * record.event_ticket_id.price * weight
            
    
    
    

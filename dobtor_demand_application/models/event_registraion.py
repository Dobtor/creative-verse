# -*- coding: utf-8 -*-
from odoo import models, api, _


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    # region : Service Apply Action (Team) : [apply/approve/reject]
    def website_set_origin_state_cancel(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_service_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note':post.get('note',False),
                'send_mail_partner_id': self.partner_id.id,
                'partner_id': self.event_id.organizer_id.id,
                'related_partner_ids': self.partner_id.id,
                'auditor': self.env.user.id,
                 'state': 'cancel',
                # region: just rel record
                'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                'rel_id': self.event_id.event_ticket_ids[:1].id,
                # endregion
            })
            if action.auto_confirm:
                application.action_do('reject')
                application.application_cancel_notify()
        else:
            self.set_organizer_state_cancel()

    def action_service_reject_application(self, rel_model=None):
        self.with_context(force_sent_mail=False).set_organizer_state_cancel()

    def website_set_origin_state_open(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_service_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note': action.text_template,
                'send_mail_partner_id': self.partner_id.id,
                'partner_id': self.event_id.organizer_id.id,
                'auditor': self.env.user.id,
                'state': 'confirm',
                # region: just rel record
                'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                'rel_id': self.event_id.event_ticket_ids[:1].id,
                # endregion
            })
            if action.auto_confirm:
                application.action_do()
                application.application_confirm_notify()

            # 往下一個階段的初始紀錄
            action =  self.env.ref('dobtor_demand_application.action_creator_service_reject')
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note': action.apply_text_template,
                'send_mail_partner_id': self.event_id.event_creator_partner.id,
                'partner_id': self.event_id.event_creator_partner.id,
                 # region: just rel record
                'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                'rel_id': self.event_id.event_ticket_ids[:1].id,
                # endregion
            })
        else:
            self.set_organizer_state_open()

    def action_service_approve_application(self, rel_model=None):
        self.with_context(force_sent_mail=False).set_organizer_state_open()

    @api.model_create_multi
    def create(self, vals_list):
        registrations = super(EventRegistration, self).create(vals_list)
        for i, registration in enumerate(registrations):
            if registration.mode == 'demand':
                Application = self.env['request.application'].sudo()
                action =  self.env.ref('dobtor_demand_application.action_service_reject')
                if action.active:
                    application = Application.create({
                        'res_id': registration.id,
                        'action_id':action.id,
                        'note': action.apply_text_template,
                        'send_mail_partner_id': registration.event_id.organizer_id.id,
                        'partner_id': registration.partner_id.id,
                        # region: just rel record
                        'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                        'rel_id': registration.event_id.event_ticket_ids[:1].id,
                        # endregion
                    })
        return registrations
    # endregion

    # region : Service Apply Action (Team) : [apply/approve/reject]
    def website_set_demand_creator_state_cancel(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_creator_service_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note':post.get('note',False),
                'send_mail_partner_id': self.partner_id.id,
                'partner_id': self.partner_id.id,
                'related_partner_ids': self.event_id.event_creator_partner.id,
                'auditor': self.env.user.id,
                'state': 'cancel',
                # region: just rel record
                'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                'rel_id': self.event_id.event_ticket_ids[:1].id,
                # endregion
            })
            if action.auto_confirm:
                application.action_do('reject')
                application.application_cancel_notify()
        else:
            self.set_demand_creator_state_cancel()

    def action_service_creator_reject_application(self, rel_model=None):
        self.with_context(force_sent_mail=False).set_demand_creator_state_cancel()

    def website_set_demand_creator_state_open(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_creator_service_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note': action.text_template,
                'send_mail_partner_id': self.partner_id.id,
                'partner_id': self.partner_id.id,
                'related_partner_ids': self.event_id.event_creator_partner.id,
                'auditor': self.env.user.id,
                'state': 'confirm',
                # region: just rel record
                'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                'rel_id': self.event_id.event_ticket_ids[:1].id,
                # endregion
            })
            if action.auto_confirm:
                application.action_do()
                application.application_confirm_notify()

        else:
            self.set_demand_creator_state_open()

    def action_service_creator_approve_application(self, rel_model=None):
        self.with_context(force_sent_mail=False).set_demand_creator_state_open()
    # endregion 

    def creator_appeal(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_creator_appeal_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note':post.get('note',False),
                'send_mail_partner_id': self.partner_id.id,
                'partner_id': self.event_id.event_creator_partner.id,
                'related_partner_ids': self.partner_id.id,
                'auditor': self.env.user.id,
                'state': 'cancel',
                # region: just rel record
                'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                'rel_id': self.event_id.event_ticket_ids[:1].id,
                # endregion
            })
            if action.auto_confirm:
                application.action_do('reject')
                application.application_cancel_notify()
        else:
            self.action_creator_appeal()
    
    def action_service_creator_appeal_application(self, rel_model=None):
        self.action_creator_appeal()

    def creator_check(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_creator_appeal_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note': action.text_template,
                'send_mail_partner_id': self.partner_id.id,
                'partner_id': self.event_id.event_creator_partner.id,
                'related_partner_ids': self.partner_id.id,
                'auditor': self.env.user.id,
                'state': 'confirm',
                # region: just rel record
                'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                'rel_id': self.event_id.event_ticket_ids[:1].id,
                # endregion
            })
            if action.auto_confirm:
                application.action_do()
                application.application_confirm_notify()
        else:
            self.action_creator_check()
    
    def action_service_creator_check_application(self, rel_model=None):
        self.action_creator_check()
    

    def attendee_appeal(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_attendee_appeal_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note':post.get('note',False),
                'send_mail_partner_id': self.event_id.event_creator_partner.id,
                'partner_id': self.partner_id.id,
                'related_partner_ids': self.event_id.event_creator_partner.id,
                'auditor': self.env.user.id,
                'state': 'cancel',
                # region: just rel record
                'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                'rel_id': self.event_id.event_ticket_ids[:1].id,
                # endregion
            })
            if action.auto_confirm:
                application.action_do('reject')
                application.application_cancel_notify()
        else:
            self.action_attendee_appeal()

    def action_service_attendee_appeal_application(self, rel_model=None):
        self.action_attendee_appeal()

    def attendee_finish(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_attendee_appeal_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note': action.text_template,
                'send_mail_partner_id': self.event_id.event_creator_partner.id,
                'partner_id': self.partner_id.id,
                'related_partner_ids': self.event_id.event_creator_partner.id,
                'auditor': self.env.user.id,
                'state': 'confirm',
                # region: just rel record
                'rel_model_id': self.env.ref('event.model_event_event_ticket').id,
                'rel_id': self.event_id.event_ticket_ids[:1].id,
                # endregion
            })
            if action.auto_confirm:
                application.action_do()
                application.application_confirm_notify()
        else:
            self.action_attendee_finish()

    def action_service_attendee_finish_application(self, rel_model=None):
        self.action_attendee_finish()

    

    

    

    
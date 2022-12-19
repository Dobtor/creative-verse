# -*- coding: utf-8 -*-
import logging
from odoo import http, _
from odoo.http import request
from werkzeug import urls
from odoo.exceptions import UserError
from odoo.addons.dobtor_team.controllers.controllers import UserSelectTeam, DobtorWebsiteProfile


_logger = logging.getLogger(__name__)

class DobtorTeamProfile(DobtorWebsiteProfile):

    @http.route()
    def user_webiste_profile(self, partner_id, **kw):
        response = super().user_webiste_profile(partner_id,**kw)
        if partner_id.is_team:
            tag =  request.env.ref('dobtor_team_application.team_tag_team_publish')
            response.qcontext['team_publish'] = tag in partner_id.tag_ids
            action =  request.env.ref('dobtor_team_application.action_team_publish')

            application = request.env['request.application'].sudo().search([
                ('res_model','=', 'res.partner'),
                ('res_id','=',partner_id.id),
                ('action_id','=',action.id),
                ('state','=','draft'),
                ('mode', '=', 'action')
            ],
            limit=1)
            response.qcontext['publish_waiting_review'] = len(application)
            
            all_custom_fields = response.qcontext['custom_fields'] + response.qcontext['custom_address_fields']
            response.qcontext['required_fields_unfilled'] = [field for field in all_custom_fields if field.required and not partner_id[field.name]]
        return response

    @http.route(['/team/publish/apply'], type='json', auth="public", methods=['POST'], website=True)
    def team_publish_apply(self, **post):
        team = request.env['res.partner'].sudo().browse(post.get('partner_id',False))
        if team:
            Application = request.env['request.application'].sudo()
            action =  request.env.ref('dobtor_team_application.action_team_publish')
            # TODO 目前先寫為申請中不能再次申請
            application = Application.search([
                ('res_model','=', 'res.partner'),
                ('res_id', '=', team.id),
                ('action_id','=', action.id),
                ('state','=','draft'),
                ('mode', '=', 'action'),
            ],
            limit=1)
            if not application:
                application = Application.create({
                    'res_id': team.id,
                    'action_id':action.id,
                    'note': action.apply_text_template or post.get('note',False),
                    'partner_id': team.id,
                    'mode': 'action',
                    'related_partner_ids': request.env.ref('base.user_admin').id,
                    'send_mail_partner_id': request.env.user.partner_id.id,
                })
                application.application_apply_notify()
        return request.env['ir.ui.view']._render_template("dobtor_team_application.team_application_confirm",{})

class UserSelectTeam(UserSelectTeam):

    def team_domain(self):
        domain = super().team_domain()
        return domain + [('tag_ids', 'in', [request.env.ref('dobtor_team_application.team_tag_team_publish').id])]

    @http.route()
    def my_team(self, **post):
        response = super(UserSelectTeam, self).my_team()
        team_publish_tag = request.env.ref('dobtor_team_application.team_tag_team_publish')
        publish_action = request.env.ref('dobtor_team_application.action_team_publish')
        my_apply_or_join_teams = set((response.qcontext['apply_teams'].partner_id + response.qcontext['my_join_teams']).ids)
        
        application_team_list = request.env['request.application'].sudo().search([
            ('action_id', '=', publish_action.id),
            ('state', '=', 'draft'),
            ('mode', '=', 'action'),
        ]).mapped('res_id')
        application_teams = request.env['res.partner'].sudo().browse(application_team_list)

        my_unpublish_team_counts = len(response.qcontext['my_join_teams'].filtered(
            lambda self: self.leader_id == request.env.user.partner_id and team_publish_tag not in self.tag_ids
        ))

        response.qcontext.update({
            'team_publish_tag': team_publish_tag,
            'publish_action': publish_action,
            'application_teams': application_teams,
            'my_unpublish_team_counts': my_unpublish_team_counts,
        })

        return response

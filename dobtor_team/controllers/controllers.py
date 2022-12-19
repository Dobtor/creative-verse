# -*- coding: utf-8 -*-
import logging
import random
from odoo import http, _
from odoo.addons.http_routing.models.ir_http import unslug
from odoo.http import request
from werkzeug import urls
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.addons.dobtor_user_profile.controllers.controllers import DobtorWebsiteProfile


_logger = logging.getLogger(__name__)


class UserSelectTeam(http.Controller):

    # region: 群組加入/取消申請、退出群組 (modal popup、功能)
    # TODO: 應該可以做整合，但需要時間
    @http.route(['/team/apply_confirm'], type='json', auth='user', methods=['POST'], website=True)
    def team_apply_confirm(self, *args, **post):
        if post.get('organizer_id', False):
            organizer_id = post.get('organizer_id', False)
            team = request.env['res.partner'].sudo().browse(organizer_id)
            partner = request.env.user.partner_id
            team.sudo().write({
                'apply_ids': [(0, 0, {
                    'member_id': partner.id
                })] 
            })
            partner.notify_apply_to_join(team)
        return request.env['ir.ui.view']._render_template("dobtor_team.apply_confirm_modal")

    @http.route(['/team/cancel_apply_modal'], type='json', auth='user', methods=['POST'], website=True)
    def team_cancel_apply_modal(self, *args, **post):
        return request.env['ir.ui.view']._render_template("dobtor_team.apply_cancel_modal")

    @http.route(['/team/cancel_apply_confirm'], type='json', auth='user', methods=['POST'], website=True)
    def team_cancel_apply_confirm(self, **post):
        if post.get('organizer_id', False):
            organizer_id = post.get('organizer_id', False)
            team = request.env['res.partner'].sudo().browse(organizer_id)
            partner = request.env.user.partner_id
            request.env['member.apply.list'].sudo().search([('partner_id', '=', team.id), ('member_id', '=', partner.id)]).unlink()
        return True

    @http.route(['/team/leave_modal'], type='json', auth='user', methods=['POST'], website=True)
    def team_leave_modal(self, *args, **post):
        return request.env['ir.ui.view']._render_template("dobtor_team.leave_modal")

    @http.route(['/team/leave_confirm'], type='json', auth='user', methods=['POST'], website=True)
    def team_leave_confirm(self, **post):
        if post.get('organizer_id', False):
            organizer_id = post.get('organizer_id', False)
            team = request.env['res.partner'].sudo().browse(organizer_id)
            partner = request.env.user.partner_id

            team.sudo().update({
                'assistant_ids': [(6, 0, (team.assistant_ids - partner).ids)],
                'team_member_ids': [(6, 0, (team.team_member_ids - partner).ids)],
            })
            team.notify_leave_team(partner)
        return True
    # endregion

    @http.route(['/member/option'], type='json', auth='user', methods=['POST'], website=True)
    def member_option(self, **post):
        if post.get('organizer_id', False) and post.get('member_id', False):
            if post.get('approve', False) or post.get('reject', False):
                team = request.env['res.partner'].sudo().browse(post.get('organizer_id', False))
                partner = request.env['res.partner'].sudo().browse(post.get('member_id', False))
                if post.get('approve', False):
                    team.action_member_approve(partner, post)
                if post.get('reject', False):
                    team.action_member_reject(partner, post)
            else:
                organizer_id = int(post.get('organizer_id')) if post.get('organizer_id', False) else False
                team = request.env['res.partner'].sudo().browse(organizer_id)
                team_members = (team.assistant_ids + team.team_member_ids).ids

                member_id = int(post.get('member_id')) if post.get('member_id', False) else False
                if member_id in team_members:
                    member = request.env['res.partner'].sudo().browse(member_id)

                    if post.get('to_assistant', False):
                        new_assistants, new_members = team.action_member_to_assistant(member, post)

                    if post.get('to_member', False):
                        new_assistants, new_members = team.action_member_to_member(member, post)
  
                    if post.get('kick', False):
                        new_assistants, new_members = team.action_member_kick(member, post)
                        
                    if bool(post.get('to_assistant', False)) ^ bool(post.get('to_member', False)) ^ bool(post.get('kick', False)):
                        if new_assistants != False:
                            team.update({
                                'assistant_ids': [(6, 0, new_assistants.ids)],
                            })
                        if new_members != False:
                            team.update({
                                'team_member_ids': [(6, 0, new_members.ids)],
                            })
                            

        return True

    def get_related_team(self,team):
        return request.env['res.partner'].search([('parents_id', '=', team.id)])

    @http.route('/<model("res.partner"):team>/list', type='http', auth="user", website=True)
    def team_list(self, team, **post):
        parents = request.env['res.partner'].search([('parents_id', 'parent_of', team.id)])
        parents_sort_array = []

        if post.get('main_team_id'):
            main_parents = request.env['res.partner'].search([('is_team', '=', True), ('id', '!=', int(post.get('main_team_id'))), ('parents_id', 'parent_of', int(post.get('main_team_id')))])
            parents -= main_parents
        
        while len(parents_sort_array) < len(parents):
            if parents.filtered(lambda self: self.parents_id not in parents) and parents.filtered(lambda self: self.parents_id not in parents) not in parents_sort_array:
                parents_sort_array.append(parents.filtered(lambda self: self.parents_id not in parents))
            elif parents.filtered(lambda self: self.parents_id == parents_sort_array[-1]):
                parents_sort_array.append(parents.filtered(lambda self: self.parents_id == parents_sort_array[-1]))

        related_team = self.get_related_team(team)
        vals = {
            'team': team,
            'parents': parents_sort_array,
            'main_team_id': post.get('main_team_id'),
            'related_team': related_team,
        }

        return request.render("dobtor_team.team_info", vals)
    
    def get_joined_teams(self):
        return request.env['res.partner'].search([
            '|','|',
            ('team_member_ids', 'in', request.env.user.partner_id.id),
            ('leader_id', '=', request.env.user.partner_id.id),
            ('assistant_ids', 'in', request.env.user.partner_id.ids)
        ])

    @http.route('/my/team/member/list', type='http', auth="user", website=True)
    def my_team_member_list(self, **post):
        partner = request.env.user.partner_id
        my_join_teams = self.get_joined_teams()
        sm_team = []

        team_id = post.get('team_id')
        if team_id:
            team_id = unslug(team_id)[1] or 0

            if int(team_id) in my_join_teams.ids:
                team_display = request.env['res.partner'].browse(int(team_id))
        else:
            team_display = my_join_teams[:1]

        for parent_team in team_display:
            parents = request.env['res.partner'].search([('parents_id', 'parent_of', parent_team.id)])
            sm_team.append({
                'team': parent_team, 
                'parents': parents,
            })

        vals = {
            'my_join_teams': my_join_teams,
            'team': team_display,
            'is_leader': partner.id == team_display.leader_id.id,
            'is_assistant': partner.id in team_display.assistant_ids.ids,
            'is_member': partner.id in team_display.team_member_ids.ids,
            'team_select': True,
            'position': 'my_team_member_list',

            # TODO: 教會覆寫還未進行修正所以暫時留著，否則會導致教會那邊出現錯誤
            'sm_team' : sm_team,
        }

        return request.render("dobtor_team.team_member_list", vals)
    
    def leader_team_info(self):
        partner = request.env.user.partner_id
        # my_leader_team = request.env['res.partner'].search([('is_team', '=', True), ('leader_id', '=', partner.id)])
        teams = request.env['res.partner'].search([('is_team', '=', True)])
        my_leader_team = teams.filtered(lambda team: team.leader_id == partner or partner.id in team.assistant_ids.ids)
        all_team_info = []

        for team in my_leader_team:
            parents = request.env['res.partner'].search([('parents_id', '=', team.id)])
            if parents:
                all_team_info.append({'team': team, 'parents': parents})
        return all_team_info

    @http.route('/my/team/list', type='http', auth="user", website=True)
    def my_team_list(self, **post):
        all_team_info = self.leader_team_info()
        vals = {
            'all_team_info' : all_team_info,
            'post':post,
            'position': 'my_team_list',
        }
        return request.render("dobtor_team.team_list", vals)

    @http.route('/my/team', type='http', auth="user", website=True)
    def my_team(self, **post):
        Team = request.env['res.partner']
        partner = request.env.user.partner_id
        apply_teams = request.env['member.apply.list'].sudo().search([
            ('partner_id', '!=', False),
            ('partner_id.is_team', '=', True),
            ('member_id', '=', partner.id),
        ])
        my_join_teams = Team.search([
            '&',
            ('is_team', '=', True),
            '|', '|',
            ('leader_id', '=', partner.id),
            ('assistant_ids', 'in', partner.id),
            ('team_member_ids', 'in', partner.id),
        ])
        values = {
            'partner': partner,
            'apply_teams': apply_teams,
            'my_join_teams': my_join_teams,
            'position': 'my_team',
        }
        return request.render("dobtor_team.my_team_index", values)

    def team_domain(self):
        return [('is_team', '=', True)]

    @http.route(['/team', '/team/page/<int:page>'], type='http', auth="user", website=True)
    def team_homepage(self, page=1, **post):
        Team = request.env['res.partner']
        step = 12  # Number of events per page
        domain = self.team_domain()
        team_count = Team.search_count(domain)
        pager = request.website.pager(
            url="/team",
            url_args=post,
            total=team_count,
            page=page,
            step=step,
            scope=5)

        teams = Team.search(domain, limit=step, offset=pager['offset'])

        values = {
            'teams': teams,
            'pager': pager,
        }

        return request.render("dobtor_team.team_index", values)

    @http.route('/team/upload_team', type='json', auth="user", methods=['POST'], website=True)
    def team_upload(self, **post):
        values = dict((fname, post[fname])
                      for fname in self._get_valid_team_post_values()
                      if post.get(fname))

        try:
            values['company_type'] = 'company'
            values['is_team'] = True
            values['leader_id'] = request.env.user.partner_id.id
            
            team = request.env['res.partner'].sudo().create(values)

        except UserError as e:
            _logger.error(e)
            return {'error': e.args[0]}
        except Exception as e:
            _logger.error(e)
            return {
                'error':
                _(
                    'Internal server error, please try again later or contact administrator.\nHere is the error message: %s',
                    e)
            }

        return {
            'url': "/user/profile/%s" % team.id,
        }
    
    def _get_valid_team_post_values(self):
        return [
            'name', 'profile_content', 'image_1920',
        ]

    # region: 群組資訊編輯
    @http.route(['/team/template/display'], type='json', auth='user', methods=['POST'], website=True)
    def team_tempalte_display(self, team_id, info_edit=False, **post):
        partner = request.env['res.partner'].sudo().browse(int(team_id))
        current_user = request.env.user.partner_id
        team_distinction = request.env.ref('dobtor_team.fields_show_distinction_team_data')
        custom_fields = request.env['partner.required.fields'].sudo().search([('show_in_where_ids', 'in', team_distinction.id)])
        custom_address_fields = custom_fields.filtered(lambda self: self.name in ['country_id', 'state_id', 'city', 'zip', 'street'])

        values = {
            'partner': partner, 
            'is_leader': current_user.id == partner.leader_id.id,
            'is_assistant': current_user.id in partner.assistant_ids.ids,
            'custom_fields': custom_fields - custom_address_fields,
            'custom_address_fields': custom_address_fields,
            'info_edit': info_edit
        }

        special_field = (custom_fields - custom_address_fields).filtered(lambda self: self.type in ('selection', 'many2one'))
        if special_field:
            partner_model = request.env['ir.model'].sudo().search([('model', '=', 'res.partner')])
            values['special_field_data'] = {}

            for field in special_field:
                if field.type == 'selection':
                    values['special_field_data'].update({
                        field.name: request.env['ir.model.fields'].sudo().search([('model_id', '=', partner_model.id),('name', '=', field.name)]).selection_ids,
                    })
                elif field.type == 'many2one':
                    values['special_field_data'].update({
                        field.name: request.env[field.relation].search(safe_eval(field.domain) if field.domain else []),
                    })

        if custom_address_fields:
            for field in custom_address_fields:
                values.update({
                    'custom_' +  field.name: {
                        'field': field,
                        'data': request.env[field.relation].search(safe_eval(field.domain) if field.domain else []) if field.type == 'many2one' else False,
                    },
                })

        return request.env['ir.ui.view']._render_template("dobtor_team.db-team-information", values),

    def random_team_email_verification_code(self):
        chars = '0123456789'
        return ''.join(random.SystemRandom().choice(chars) for _ in range(4))

    @http.route('/team/send_email', type='json', method=['POST'], auth="public", website=True, csrf=True)
    def team_send_email(self, **post):
        website = request.env['website'].sudo().browse(
            request.env.context['website_id'])
        email = post.get('email')
        template = request.env.ref(
            'dobtor_team.mail_template_team_factor_auth',
            raise_if_not_found=False)
        if website and template and email:
            try:
                factor_auth = self.random_team_email_verification_code()
                request.session['email_team_factor_auth'] = factor_auth
                email_values = {'email_to': email}
                template.sudo().with_context(
                    factor_auth=factor_auth).send_mail(
                        website.id,
                        email_values=email_values,
                        force_send=True,
                        raise_exception=False)
                return '1'
            except Exception as e:
                _logger.error('Here is error %s', e)
                return
        return

    @http.route(['/team/edit/save'], type='json', auth='user', methods=['POST'], website=True, csrf=True)
    def team_edit_save(self, team_id, **post):
        partner = request.env['res.partner'].sudo().browse(int(team_id))
        country_taiwan = request.env.ref('base.tw')
        error_field = []
        error_message = []
        values = dict((fname, post[fname]) for fname in self._get_valid_team_info_post_values())

        if 'country_id' in values.keys():
            values['country_id'] = int(values['country_id']) if values['country_id'] else False
            if not values['country_id']:
                values['country_id'] = country_taiwan.id

            # TODO: 選擇國外時，填寫的護照名稱、號碼，不知道還有沒有需要使用，這裡先進行隱藏，若確定沒用到時可進行移除
            # if int(values['country_id']) != country_taiwan.id:
            #     values['passport_name'] = post['passport_name']
            #     values['passport_number'] = post['passport_number']
            #     if not post['passport_name'] or not post['passport_number']:
            #         error_message.append(_("Please fill in the passport name/number correctly."))
            # else:
            #     values['passport_name'] = False
            #     values['passport_number'] = False

        if 'state_id' in values.keys():
            values['state_id'] = int(values['state_id']) if values['state_id'] else False

        if 'email' in values.keys() and partner.email != values['email']:
            if not request.session.get('email_team_factor_auth', None):
                # error_field.append('email_verify_code')
                error_message.append(_("Email to change, you need to enter the verification code."))
            elif post.get('email_verify_code') != request.session.get('email_team_factor_auth', None):
                # error_field.append('email_verify_code')
                error_message.append(_("Verification code error, please re-enter."))

        if error_message:
            return {'error_field': error_field, 'error_message': error_message}
        else:
            partner.sudo().write(values)
            return {'partner': partner}

    def _get_valid_team_info_post_values(self):
        team_distinction = request.env.ref('dobtor_team.fields_show_distinction_team_data')
        custom_fields = request.env['partner.required.fields'].sudo().search([('show_in_where_ids', 'in', team_distinction.id)])
        return [field.name for field in custom_fields]
    # endregion
        
class DobtorWebsiteProfile(DobtorWebsiteProfile):

    def __profile_edit_check(self, partner):
        if partner.is_team:
            return partner.leader_id == request.env.user.partner_id
        return super(DobtorWebsiteProfile, self).__profile_edit_check(partner)

    @http.route()
    def user_webiste_profile(self, partner_id, **kw):
        partner = partner_id
        if partner_id.is_team:
            current_user = request.env.user.partner_id
            values = self._prepare_user_profile_layout_values(partner_id.id)
            team_distinction = request.env.ref('dobtor_team.fields_show_distinction_team_data')
            custom_fields = request.env['partner.required.fields'].sudo().search([('show_in_where_ids', 'in', team_distinction.id)])
            custom_address_fields = custom_fields.filtered(lambda self: self.name in ['country_id', 'state_id', 'city', 'zip', 'street'])

            values.update({
                'is_leader': current_user.id == partner.leader_id.id,
                'is_assistant': current_user.id in partner.assistant_ids.ids,
                'is_member': current_user.id in partner.team_member_ids.ids,
                'audit': request.env['member.apply.list'].sudo().search([('partner_id', '=', partner.id), ('member_id', '=', current_user.id)]),
                'custom_fields': custom_fields - custom_address_fields,
                'custom_address_fields': custom_address_fields,
            })

            if custom_address_fields:
                for field in custom_address_fields:
                    values.update({
                        'custom_' +  field.name: {
                            'field': field,
                            'data': request.env[field.relation].search(safe_eval(field.domain) if field.domain else []) if field.type == 'many2one' else False,
                        },
                    })

            return request.render("dobtor_team.team_portal_profile", values)
        else:
            response = super(DobtorWebsiteProfile, self).user_webiste_profile(partner_id, **kw)
            partner_join_teams = request.env['res.partner'].search([
                ('is_team', '=', True),
                '|', '|',
                ('leader_id', '=', partner.id),
                ('assistant_ids', 'in', partner.id),
                ('team_member_ids', 'in', partner.id),
            ])
            apply_teams = request.env['member.apply.list'].sudo().search([
                ('partner_id', '!=', False),
                ('partner_id.is_team', '=', True),
                ('member_id', '=', partner.id),
            ]).partner_id

            # TODO: 這段為抓取該群組所有的上層群組有哪些，但現在不管是(編輯資訊、管理成員)都以當前群組的管理層為主進行操作，為求統一，所以
            # 先將可瀏覽群組成員聯繫資料限縮在當前群組管理層，後續是否需要修改待討論
            # partner_join_teams_parents = request.env['res.partner'].search([('parents_id', 'parent_of', partner_join_teams.ids)])

            partner_join_teams_managers = sum([team.leader_id.ids + team.assistant_ids.ids for team in partner_join_teams + apply_teams], [])
            response.qcontext['partner_join_teams_managers'] = set(partner_join_teams_managers)
            
            return response

    @http.route()
    def profile_desc_edit_modal(self, partner, **post):
        if partner.is_team:
            values = {
                'partner': partner,
                'can_edit': partner.leader_id == request.env.user.partner_id,
            }
            return request.env['ir.ui.view']._render_template("dobtor_user_profile.profile_desc_edit_modal", values)
        return super(DobtorWebsiteProfile, self).profile_desc_edit_modal(partner, **post)

    @http.route()
    def profile_desc_edit(self, partner, **post):
        if partner.is_team:
            if partner.leader_id == request.env.user.partner_id:
                partner.sudo().write({
                    'profile_description': post.get('profile_description', False)
                })
            return True
        return super(DobtorWebsiteProfile, self).profile_desc_edit(partner, **post)

    @http.route()
    def profile_about_edit_tempalte(self, partner, about_edit=False, **post):
        if partner.is_team:
            values = {
                'partner': partner,
                'about_edit': about_edit,
                'is_leader': partner.leader_id == request.env.user.partner_id,
            }
            return request.env['ir.ui.view']._render_template("dobtor_team.db-team-about", values)
        return super(DobtorWebsiteProfile, self).profile_about_edit_tempalte(partner, about_edit, **post)
    
    @http.route()
    def profile_about_edit(self, partner, **post):
        if partner.is_team:
            if partner.leader_id == request.env.user.partner_id:
                partner.sudo().write({
                    'profile_content': post.get('profile_content', False), 
                })
            return True
        return super(DobtorWebsiteProfile, self).profile_about_edit(partner, **post)
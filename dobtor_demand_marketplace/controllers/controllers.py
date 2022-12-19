# -*- coding: utf-8 -*-
from odoo import fields, http, _
from odoo.http import request
from odoo.osv import expression
from odoo.addons.dobtor_event_team.controllers.controllers import DobtorWebsiteProfile
from odoo.addons.dobtor_demand.controllers.controllers import WebsiteDemand
import json
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, date, timedelta
import pytz



class DobtorDemandMarketplace(http.Controller):

    @http.route('/team/demand', type='http', auth="user", website=True)
    def team_demand(self, **post):
        post.setdefault('search', '')
        partner = request.env.user.partner_id
        cancelled_stage = request.env['event.stage'].with_context(lang='en_US').sudo().search([('name', '=', 'Cancelled')])

        team_domain = partner.check_access_rights_common_domain() + partner.operation_3_domain()
        teams = request.env['res.partner'].sudo().search(team_domain)

        current_team_id = int(post.get('team')) if post.get('team') else teams[:1].id

        domain = expression.AND([
            [('mode', '=', 'demand')],
            [('organizer_id', '=', current_team_id)],
        ])

        if post['search']:
            domain = expression.AND([
                domain,
                [('name', 'ilike', post['search'])]])
        
        demands = request.env['event.demand'].sudo().search(domain)
        
        values = {
            'partner': partner,
            'demands': demands,
            'teams': teams,
            'searches': post,
            'cancelled_stage': cancelled_stage,
            'position': 'team_demand',
        }

        return request.render("dobtor_demand_marketplace.team_demand", values)

    @http.route(['/team_demand/option'], type='json', auth='user', methods=['POST'], website=True)
    def team_demand_option(self, **post):
        if post.get('demand_id', False):

            if post.get('approve', False) or post.get('reject', False):
                team_demand = request.env['event.demand'].sudo().browse(int(post.get('demand_id')))

                if post.get('approve', False):
                    team_demand.set_state_open(post)
                if post.get('reject', False):
                    team_demand.set_state_cancel(post)

        return True

    @http.route(['/team_demand/service_option'], type='json', auth='user', methods=['POST'], website=True)
    def team_demand_service_option(self, **post):
        if post.get('registration_id', False):

            if post.get('approve', False) or post.get('cancel', False) or post.get('appeal', False):
                partner = request.env.user.partner_id
                registration = request.env['event.registration'].sudo().browse(int(post.get('registration_id')))

                if registration.partner_id == partner:
                    if registration.demand_creator_state == 'open':
                        if post.get('approve', False):
                            registration.attendee_finish(post)
                        if post.get('appeal', False):
                            registration.attendee_appeal(post)
                    else:
                        if post.get('cancel', False):
                            registration.action_cancel()

        return True

    @http.route(['/team_demand/body_option'], type='json', auth='user', methods=['POST'], website=True)
    def team_demand_body_option(self, **post):
        if post.get('registration_id', False):

            if post.get('approve', False) or post.get('reject', False):
                # team_demand = request.env['event.demand'].sudo().browse(int(post.get('demand_id')))
                partner = request.env.user.partner_id
                registration = request.env['event.registration'].sudo().browse(int(post.get('registration_id')))
                event = registration.event_id
                is_team_manager = event.organizer_id.leader_id.id == partner.id or partner.id in event.organizer_id.assistant_ids.ids

                if registration.organizer_state == 'open' and (event.event_creator_partner.id == partner.id or is_team_manager):
                    if post.get('approve', False):
                        registration.website_set_demand_creator_state_open(post)
                    if post.get('reject', False):
                        registration.website_set_demand_creator_state_cancel(post)
        return True

    @http.route(['/team_demand/creator_check_option'], type='json', auth='user', methods=['POST'], website=True)
    def team_demand_creator_check_option(self, **post):
        if post.get('registration_id', False):

            if post.get('approve', False) or post.get('appeal', False):
                partner = request.env.user.partner_id
                registration = request.env['event.registration'].sudo().browse(int(post.get('registration_id')))
                event = registration.event_id
                is_team_manager = event.organizer_id.leader_id.id == partner.id or partner.id in event.organizer_id.assistant_ids.ids

                if event.event_creator_partner.id == partner.id or is_team_manager:
                    if post.get('approve', False):
                        registration.creator_check(post)
                    if post.get('appeal', False):
                        registration.creator_appeal(post)
        return True

    @http.route(['/team_demand/<model("event.event"):demand>/report'], auth="user", website=True)
    def team_demand_report(self, demand, search=None, **post):
        cancelled_stage = request.env['event.stage'].with_context(lang='en_US').search([('name', '=', 'Cancelled')])
        registration_domain = [('event_id', '=', demand.id)]
        if search:
            registration_domain += [('name', 'ilike', search)]
        registrations = request.env['event.registration'].search(registration_domain)
        return request.render("dobtor_demand_marketplace.custom_demand_report_full", { 'event': demand, 'registrations': registrations, 'search': search, 'cancelled': cancelled_stage,})

    @http.route(['/team_demand/service_audit_option'], type='json', auth='user', methods=['POST'], website=True)
    def team_demand_service_audit_option(self, **post):
        if post.get('registration_id', False):

            if post.get('approve', False) or post.get('reject', False):
                partner = request.env.user.partner_id
                registration = request.env['event.registration'].sudo().browse(int(post.get('registration_id')))
                event = registration.event_id

                team_domain = partner.check_access_rights_common_domain() + partner.operation_3_domain()
                teams = request.env['res.partner'].sudo().search(team_domain)

                if event.mode == 'demand' and event.organizer_id.id in teams.ids:
                    if post.get('approve', False):
                        registration.website_set_origin_state_open(post)
                    if post.get('reject', False):
                        registration.website_set_origin_state_cancel(post)

        return True


    def _get_valid_demand_post_values(self):
        return [
            'name', 'subtitle', 'date_begin', 'date_end', 'is_team', 'is_show_public', 'is_use_team_wallet',
            'event_organizer', 'description', 'cover_properties',
            'event_default_cover', 'event_organizer_disabled', 'event_address_disabled', 'event_price_disabled','organizer_id',

            # region: online address
            'online_address', 'event_address',
            # endregion

            # region: offline address
            'offline_address', 'state_id', 'city', 'zip', 'street',
            # endregion
        ]
    
    def _event_upload_cover_properties(self, event):
        return {
            "background-image": "url(/web/image/event.event/%s/event_default_cover)" %(event.id),
            "background_color_class": "",
            "background_color_style": "background-color: #CEDEE7;",
            "opacity": "0.4",
            "resize_class":"o_half_screen_height o_record_has_cover",
            "text_align_class":"",
        }
    
    def _create_or_get_event_tag(self, tag_ids):
        tags = []
        for tag in tag_ids:
            if tag[0] == 0:
                new_tag = request.env['event.tag'].create({
                    'name': tag[1]['name'],
                    'category_id': request.env.ref('dobtor_event.event_type_tag_data').id,
                })
                tags.append([4, new_tag.id])
            else:
                tags.append(tag)
        return tags
    
    def __parpare_event_ticket(self, values, event, post):
        ticket_values = {
            'name': values['name'],
            'event_id': event.id,
            'price': post.get('price'),
            'pricing_method': post.get('pricing_method'),
            'description': values['name'],
        }

        if all(key in values.keys() for key in ("date_begin", "date_end")):
            ticket_values.update({
                'start_sale_date': values['date_begin'],
                'end_sale_date': values['date_end'],
            })
                
        return ticket_values
    
    @http.route(['/demand/portal/organizer/search_read'], type='json', auth='user', methods=['POST'], website=True)
    def demand_portal_organizer_search_read(self, fields):
        partner = request.env.user.partner_id
        domain = partner.check_access_rights_common_domain() + partner.operation_7_domain()
        return {
            'read_results':request.env['res.partner'].sudo().search_read(domain, fields)
        }

    @http.route(['/demand/tag/search_read'], type='json', auth='user', methods=['POST'], website=True)
    def event_tag_search_read(self, fields, domain):
        can_create = request.env['event.tag'].check_access_rights('create', raise_exception=False)
        search_domain = domain

        return {
            'read_results': request.env['event.tag'].search_read(search_domain, fields),
            'can_create': can_create,
        }


    @http.route('/demand/upload_demand',type='json',auth="user",methods=['POST'],website=True, csrf=True)
    def upload_demand(self, **post):
        values = dict((fname, post[fname])for fname in self._get_valid_demand_post_values() if post.get(fname))
        # _logger.info('Upload Demand Value %s' % values)
        try:
            values['mode'] = 'demand'
            values['seats_available'] = 1000
            values['website_id'] = request.website.id
            if 'organizer_id' not in values.keys():
                values['organizer_id'] = False

            if 'is_show_public' not in values.keys():
                values['is_show_public'] = False

            if 'date_end' in post.keys() and post.get('date_end') < post.get('date_begin'):
                return {'error': _('活動開始日期不可超過結束日期')}

            demand = request.env['event.demand'].with_context(
                request.context or {}).sudo().create(values)
            event = demand.event_id

            if post.get('tag_ids'):
                tags = self._create_or_get_event_tag(post.get('tag_ids'))
                event.update({
                    'tag_ids': tags
                })

            # region : handle prining
            if not post.get('price'):
                event.update({
                    'auto_confirm': True,
                })

            if post.get('price'):
                __ticket_data = self.__parpare_event_ticket(values, event, post)
                if post.get('request_qty'):
                    __ticket_data.update({'request_qty' : post.get('request_qty')})
                if post.get('min_request_unit'):
                    __ticket_data.update({'min_request_unit' : post.get('min_request_unit')})
                # Handle : 若 website 顯示的 pricelist 所帶的幣別與(創建活動指定公司幣別/公司幣別)不同, 需做轉換
                website = request.env['website'].get_current_website()
                company_id = event.company_id or request.env.company
                currency = company_id.currency_id
                if len(website.currency_id) != 0 and website.currency_id.id != currency.id:
                    __ticket_data.update({'price': website.currency_id._convert(int(post.get('price')),
                        currency,
                        company_id,
                        fields.Date.today())})
                ticket = request.env['event.event.ticket'].sudo().create(__ticket_data)
                
                # 處理預付款
                so_id = demand.computer_downpay()
                if so_id:
                    if post.get('is_use_team_wallet'):
                        so_id.partner_id = demand.organizer_id
                    so_id.with_context(is_mixed=False).action_wallet_pay()
                    # 如果不夠就沒辦法行情 wallet_txn_id
                    if not so_id.wallet_txn_id:
                        lower = so_id.partner_id.get_partner_min_value()
                        amount = so_id.amount_total 
                        if len(website.currency_id) != 0 and website.currency_id.id != currency.id:
                            amount = website.currency_id._convert(amount, 
                                currency,
                                company_id,
                                fields.Date.today())
                        missing_amount = amount - so_id.partner_id.wallet_current + lower
                        request.env.cr.rollback()
                        return {
                            'error': _('The balance is less than %s points, and the demand cannot be established') %(missing_amount),
                            'use_team_wallet' : True,
                        }
                        
            # endregion

            if post.get('need_register'):
                if post['need_register'] == '0':
                    event.update({
                        'need_register': False,
                    })
                elif post['need_register'] == '1':
                    if post.get('behalf_register') == '0':
                        event.update({
                            'behalf_register': False,
                        })
                    if not post.get('n_login_register'):
                        event.update({
                            'n_login_register': False,
                        })
        except UserError as e:
            _logger.error(e)
            request.env.cr.rollback()
            return {'error': e.args[0]}
        except Exception as e:
            _logger.error(e)
            request.env.cr.rollback()
            return {
                'error':
                _(
                    'Internal server error, please try again later or contact administrator.\nHere is the error message: %s',
                    e)
            }

        return {
            'url': "/demand/%s" % slug(event),
        }

    @http.route('/demand/edit_demand',type='json',auth="user",methods=['POST'],website=True, csrf=True)
    def edit_demand(self, **post):
        partner = request.env.user.partner_id
        demand = request.env['event.demand'].browse(int(post.get('demand_id', False)))

        if demand.event_creator_partner.id == partner.id:
            values = dict((fname, post[fname])for fname in self._get_valid_demand_post_values() if post.get(fname))

            try:
                if 'date_end' in post.keys() and post.get('date_end') < post.get('date_begin'):
                    return {'error': _('活動開始日期不可超過結束日期')}

                if 'organizer_id' not in values.keys():
                    values['organizer_id'] = False
                    
                if 'is_show_public' not in values.keys():
                    values['is_show_public'] = False
                
                if post.get('re_edit'):
                    values['state'] = 'draft'

                date_begin = values.pop('date_begin', None)
                date_end = values.pop('date_end', None)
                # TODO: demand write編輯會觸發event write函式，但帶入的dict會被event write個別寫入 (該問題待討論)
                demand.sudo().write(values)
                event = demand.event_id.sudo()

                if date_begin and date_end:
                    event.write({
                        'date_begin': date_begin,
                        'date_end': date_end,
                    })

                if post.get('tag_ids'):
                    tags = self._create_or_get_event_tag(post.get('tag_ids'))
                    event.update({
                        'tag_ids': tags
                    })

                # region : handle prining
                if not post.get('price'):
                    event.update({
                        'auto_confirm': True,
                    })

                if post.get('price'):
                    __ticket_data = self.__parpare_event_ticket(values, event, post)
                    if post.get('request_qty'):
                        __ticket_data.update({'request_qty' : post.get('request_qty')})
                    if post.get('min_request_unit'):
                        __ticket_data.update({'min_request_unit' : post.get('min_request_unit')})
                    # Handle : 若 website 顯示的 pricelist 所帶的幣別與(創建活動指定公司幣別/公司幣別)不同, 需做轉換
                    website = request.env['website'].get_current_website()
                    company_id = event.company_id or request.env.company
                    currency = company_id.currency_id
                    if len(website.currency_id) != 0 and website.currency_id.id != currency.id:
                        __ticket_data.update({'price': website.currency_id._convert(int(post.get('price')),
                            currency,
                            company_id,
                            fields.Date.today())})
                    event.event_ticket_ids[:1].sudo().write(__ticket_data)
                    
                    # 處理預付款
                    so_id = demand.sudo().computer_downpay()
                    if so_id:
                        if post.get('is_use_team_wallet'):
                            so_id.partner_id = demand.organizer_id
                        so_id.with_context(is_mixed=False).action_wallet_pay()
                        # 如果不夠就沒辦法行情 wallet_txn_id
                        if not so_id.wallet_txn_id:
                            lower = so_id.partner_id.get_partner_min_value()
                            missing_amount = so_id.amount_total - so_id.partner_id.wallet_current + lower
                            request.env.cr.rollback()
                            return {
                                'error': _('The balance is less than %s points, and the demand cannot be established') %(missing_amount),
                                'use_team_wallet' : True,
                            }
                            
                # endregion

                # region : 欄位移除
                for field in ['event_address_disabled', 'online_address', 'offline_address', 'subtitle', 'description', 'is_show_public']:
                    if not post.get(field) and event[field]:
                        event.update({
                            field : False,
                        })
                # endregion

                if post.get('need_register'):
                    if post['need_register'] == '0':
                        event.update({
                            'need_register': False,
                        })
                    elif post['need_register'] == '1':
                        if post.get('behalf_register') == '0':
                            event.update({
                                'behalf_register': False,
                            })
                        if not post.get('n_login_register'):
                            event.update({
                                'n_login_register': False,
                            })
            except UserError as e:
                _logger.error(e)
                request.env.cr.rollback()
                return {'error': e.args[0]}
            except Exception as e:
                _logger.error(e)
                request.env.cr.rollback()
                return {
                    'error':
                    _(
                        'Internal server error, please try again later or contact administrator.\nHere is the error message: %s',
                        e)
                }

            return {
                'url': "/demand/%s" % slug(event),
            }
        

    @http.route('/my/service', type='http', auth="user", website=True)
    def my_service(self, **post):
        partner = request.env.user.partner_id

        team_domain = partner.check_access_rights_common_domain() + partner.operation_3_domain()
        teams = request.env['res.partner'].sudo().search(team_domain)
        
        demands = request.env['event.demand'].sudo().search([
            ('mode', '=', 'demand'),
            ('registration_ids.partner_id', '=', partner.id),
        ])

        values = {
            'partner': partner,
            'demands': demands,
            'teams': teams,       
            'position': 'my_service',
        }
        return request.render("dobtor_demand_marketplace.my_service", values)

    @http.route('/service/audit', type='http', auth="user", website=True)
    def service_audit(self, **post):
        post.setdefault('search', '')
        partner = request.env.user.partner_id

        team_domain = partner.check_access_rights_common_domain() + partner.operation_3_domain()
        teams = request.env['res.partner'].sudo().search(team_domain)

        current_team_id = int(post.get('team')) if post.get('team') else teams[:1].id

        domain = expression.AND([
            [('mode', '=', 'demand')],
            [('organizer_id', '=', current_team_id)],
            [('state', '=', 'open')],
        ])
        
        if post['search']:
            domain = expression.AND([
                domain,
                [('name', 'ilike', post['search'])]])
                
        demands = request.env['event.demand'].sudo().search(domain)
        
        values = {
            'partner': partner,
            'demands': demands,
            'teams': teams,
            'searches': post,
            'position': 'service_audit',
        }

        return request.render("dobtor_demand_marketplace.service_audit", values)

class DobtorWebsiteProfile(DobtorWebsiteProfile):

    @http.route()
    def user_webiste_profile(self, partner_id, **kw):
        res = super(DobtorWebsiteProfile, self).user_webiste_profile(partner_id, **kw)

        if partner_id.is_team:
            res.qcontext['team_demands'] = request.env['event.event'].sudo().search([
                ('mode', '=', 'demand'),
                ('organizer_id', '=', partner_id.id),
            ])

        return res

class WebsiteDemand(WebsiteDemand):

    @http.route()
    def my_demand(self, **post):
        partner = request.env.user.partner_id

        team_domain = partner.check_access_rights_common_domain() + partner.operation_3_domain()
        teams = request.env['res.partner'].sudo().search(team_domain)

        team_demand = []
        res = super(WebsiteDemand, self).my_demand(**post)

        for demand in res.qcontext['demands']:
            if demand.organizer_id and demand.state in ('open', 'closed') and demand.registration_ids.filtered(lambda self: self.organizer_state == 'open'):
                team_demand.append(demand.id)
        
        res.qcontext['teams'] = teams
        res.qcontext['team_demand'] = team_demand

        return res

    @http.route()
    def demand_content(self, demand, **post):
        response = super().demand_content(demand, **post)
        # 這邊的 Demand 引數其實是 event.event 的 Record
        # 只要是該需求中此用戶還有未勾選完成, 或是創建者有未確認者, 不給予繼續提供服務
        demand_sudo = demand.sudo() 
        registration = request.env['event.registration'].sudo()
        partner = request.env.user.partner_id
        team_member = demand_sudo.organizer_id.team_member_ids + demand_sudo.organizer_id.leader_id + demand_sudo.organizer_id.assistant_ids
        response.qcontext['is_team_user'] = partner.id in team_member.ids
        response.qcontext['has_join_team'] = partner.check_access_rights_via_team(7)
        response.qcontext['is_not_yet_finish'] = len(registration.search([
            ('event_id' , '=', demand_sudo.id),
            ('partner_id', '=', partner.id),
            ('state', '!=', 'cancel'),
            '|',
            ('is_attendee_finish', '=', False),
            ('is_creator_check', '=', False)])) > 0
        return response

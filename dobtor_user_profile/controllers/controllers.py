# -*- coding: utf-8 -*-
import logging
import random
import werkzeug
from werkzeug.exceptions import Forbidden, NotFound
from odoo import http, _
from odoo.http import request
from werkzeug import urls
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError
from urllib import parse as urlparse
from urllib.parse import parse_qs
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
# from odoo.addons.dobtor_user_signup.controllers.controllers import DobtorWebsiteSignup


_logger = logging.getLogger(__name__)

class ProfileContext(object):
    """ prepare value for profile
    
    __init__ input Arguments:
        module_list [{ output name : concrete object }] -- 
        for example : 
        module_list = [
            {'take_order_count', ConcreteSaleProfile},
            {'give_order_count', ConcretePurchaseProfile},
        ]
    """

    def __init__(self, module_list=[]):
        self.__prepare_module = module_list

    def append__prepare_module(self, moduel_list=[]):
        for module in moduel_list:
            self.__prepare_module.append(module)

    def _prepare_other_module_values(self):
        for module in self.__prepare_module:
            for key, val in module.items():
                yield {key: val._prepare_values()}

    def _prepare_user_profile_layout_values(self):
        output_value = dict()
        for __val in self._prepare_other_module_values():
            output_value.update(__val)
        return output_value


class DobtorWebsiteProfile(http.Controller):

    def random_profile_email_verification_code(self):
        chars = '0123456789'
        return ''.join(random.SystemRandom().choice(chars) for _ in range(4))

    def _prepare_user_profile_layout_values(self, partner_id):
        partner = request.env['res.partner'].sudo().browse(partner_id)
        parse_url = partner.referral_url and urlparse.quote(partner.referral_url) or '#'
        return {
            'partner': partner,
            'parse_url': parse_url,
        }

    @http.route(['/user/profile/<model("res.partner"):partner_id>'], type='http', auth="user", website=True)
    def user_webiste_profile(self, partner_id, **kw):
        values = self._prepare_user_profile_layout_values(partner_id.id)
        profile_distinction = request.env.ref('dobtor_user_profile.fields_show_distinction_profile_data')
        custom_fields = request.env['partner.required.fields'].sudo().search([('show_in_where_ids', 'in', profile_distinction.id)])
        custom_address_fields = custom_fields.filtered(lambda self: self.name in ['country_id', 'state_id', 'city', 'zip', 'street'])

        values.update({
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

        return request.render("dobtor_user_profile.portal_profile", values)

    def __profile_edit_check(self, partner):
        return partner == request.env.user.partner_id

    @http.route(['/profile/edit'], type='json', auth='user', methods=['POST'], website=True)
    def profile_edit(self, *args, **post):
        if post.get('profile_section') or post.get('image_256'):
            datas = post.get('profile_section') or post.get('image_256')
            file_size = len(datas) * 3 / 4  # base64
            if (file_size / 1024.0 / 1024.0) > 25:
                return {'error': _('File is too big. File size cannot exceed 25MB')}

        values = dict((fname, post[fname]) for fname in self._get_valid_profile_post_values() if fname in ('street', 'profile_description') and fname in post or post.get(fname))

        try:
            partner = request.env['res.partner'].browse(post.get('partner_id'))
            if self.__profile_edit_check(partner):
                partner.sudo().write(values)
            else:
                return {'error': _('Cannot edit other partner information')}
        except UserError as e:
            _logger.error(e)
            return {'error': e.args[0]}
        except Exception as e:
            _logger.error(e)
            return {'error': _('Internal server error, please try again later or contact administrator.\nHere is the error message: %s', e)}

        redirect_url = "/user/profile/%s" % slug(partner)

        return {
            'url': redirect_url,
        }

    @http.route('/profile/send_email', type='json', method=['POST'], auth="public", website=True, csrf=True)
    def profile_send_email(self, **post):
        website = request.env['website'].sudo().browse(
            request.env.context['website_id'])
        email = post.get('email')
        template = request.env.ref(
            'dobtor_user_profile.mail_template_profile_factor_auth',
            raise_if_not_found=False)
        if website and template and email:
            try:
                factor_auth = self.random_profile_email_verification_code()
                request.session['email_profile_factor_auth'] = factor_auth
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

    @http.route(['/profile/country_infos/<model("res.country"):country>'], type='json', auth="public", methods=['POST'], website=True)
    def profile_country_infos(self, country, **kw):
        return dict(
            states=[(st.id, st.name, st.code) for st in country.sudo().state_ids],
        )
    
    @http.route(['/partner/template/display'], type='json', auth='user', methods=['POST'], website=True)
    def partner_tempalte_display(self, info_edit=False, **post):
        partner = request.env.user.partner_id
        profile_distinction = request.env.ref('dobtor_user_profile.fields_show_distinction_profile_data')
        custom_fields = request.env['partner.required.fields'].sudo().search([('show_in_where_ids', 'in', profile_distinction.id)])
        custom_address_fields = custom_fields.filtered(lambda self: self.name in ['country_id', 'state_id', 'city', 'zip', 'street'])

        values = {
            'partner': partner, 
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

        return request.env['ir.ui.view']._render_template("dobtor_user_profile.db-user-information", values)

    @http.route(['/partner/edit/save'], type='json', auth='user', methods=['POST'], website=True, csrf=True)
    def partner_edit_save(self, **post):
        user = request.env.user
        partner = request.env.user.partner_id
        country_taiwan = request.env.ref('base.tw')
        error_field = []
        error_message = []
        values = dict((fname, post[fname]) for fname in self._get_valid_user_info_post_values())

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
            if not request.session.get('email_profile_factor_auth', None):
                # error_field.append('email_verify_code')
                error_message.append(_("Email to change, you need to enter the verification code."))
            elif post.get('email_verify_code') != request.session.get('email_profile_factor_auth', None):
                # error_field.append('email_verify_code')
                error_message.append(_("Verification code error, please re-enter."))

        if error_message:
            return {'error_field': error_field, 'error_message': error_message}
        else:
            partner.sudo().write(values)
            return {'partner': partner}

    def _get_valid_user_info_post_values(self):
        profile_distinction = request.env.ref('dobtor_user_profile.fields_show_distinction_profile_data')
        custom_fields = request.env['partner.required.fields'].sudo().search([('show_in_where_ids', 'in', profile_distinction.id)])
        return [field.name for field in custom_fields]

    def _get_valid_profile_post_values(self):
        return ['profile_section', 'image_256', 'name', 'street', 'profile_description']

    def _get_search_domain(self, search):
        partner = request.env.user.partner_id
        domains = [[('referrer_id', '=', partner.id)]]
        if search:
            for srch in search.split(" "):
                subdomains = [
                    [('name', 'ilike', srch)],
                ]
                domains.append(expression.OR(subdomains))

        return expression.AND(domains)

    @http.route([
        '''/my/member''',
        '''/my/member/page/<int:page>''',
    ], type='http', auth="user", website=True)
    def my_member(self, page=0, search='', **post):
        domain = self._get_search_domain(search)
        all_members = request.env['res.partner'].search(domain)
        if search:
            post["search"] = search
            
        pager = request.website.pager(url='/my/member', total=len(all_members), page=page, step=8, scope=5, url_args=post)
        offset = pager['offset']
        members = all_members[offset: offset + 8]

        vals = {
            'search': search,
            'members': members,
            'pager': pager,
            'position': 'my_partner',
        }
        return request.render("dobtor_user_profile.member_list", vals)

    # region: 編輯簡介popup、關於
    @http.route('/profile/<model("res.partner"):partner>/desc/edit/modal', type='json', auth="user", website=True)
    def profile_desc_edit_modal(self, partner, **post):
        values = {
            'partner': partner,
            'can_edit': partner == request.env.user.partner_id,
        }
        return request.env['ir.ui.view']._render_template("dobtor_user_profile.profile_desc_edit_modal", values)
    
    @http.route('/profile/<model("res.partner"):partner>/desc/edit', type='json', auth="user", methods=['POST'], website=True)
    def profile_desc_edit(self, partner, **post):
        if partner == request.env.user.partner_id:
            partner.sudo().write({
                'profile_description': post.get('profile_description', False)
            })

        return True

    @http.route(['/profile/<model("res.partner"):partner>/about/edit/template'], type='json', auth='user', methods=['POST'], website=True)
    def profile_about_edit_tempalte(self, partner, about_edit=False, **post):
        values = {
            'partner': partner, 
            'about_edit': about_edit
        }
        return request.env['ir.ui.view']._render_template("dobtor_user_profile.db-user-about", values)
    
    @http.route(['/profile/<model("res.partner"):partner>/about/edit'], type='json', auth='user', methods=['POST'], website=True, csrf=True)
    def profile_about_edit(self, partner, **post):
        if partner == request.env.user.partner_id:
            partner.sudo().write({
                'profile_content': post.get('profile_content', False), 
            })
        return True
    # endregion

# class DobtorWebsiteSignup(DobtorWebsiteSignup):

#     def popup_signup_values_extend(self):
#         values = super(DobtorWebsiteSignup, self).popup_signup_values_extend()
#         website = request.env['website'].sudo().browse(request.env.context['website_id'])
#         if website.customize_default_avatar:
#             values['image_1920'] = website.signup_default_avatar
#         if website.customize_default_section:
#             values['profile_section'] = website.signup_default_section

#         return values
# -*- coding: utf-8 -*-
# from odoo import http

import werkzeug
from werkzeug.datastructures import OrderedMultiDict
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo import fields, http, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.http import request
from odoo.osv import expression
from odoo.tools.misc import get_lang, format_date
from odoo.addons.dobtor_event.controllers.controllers import DobtorEventSaleController
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.addons.portal.controllers.web import Home
from odoo.addons.portal.controllers.portal import _build_url_w_params
from urllib import parse as urlparse
from werkzeug import urls
import logging
_logger = logging.getLogger(__name__)


class DobtorDemand(http.Controller):

    @http.route(['/demand/option'], type='json', auth='user', methods=['POST'], website=True)
    def demand_option(self, **post):
        if post.get('demand_id', False):

            if post.get('give_up', False) or post.get('closed', False):
                partner = request.env.user.partner_id
                demand = request.env['event.demand'].sudo().browse(int(post.get('demand_id')))
                
                if demand.event_creator_partner.id == partner.id:
                    if post.get('give_up', False):
                        demand.set_state_give_up(post)
                    if post.get('closed', False):
                        demand.set_state_closed(post)

        return True

class DobtorEventSaleController(DobtorEventSaleController):

    def _reg_phone_to_partner_phone(self, registration):
        return super()._reg_phone_to_partner_phone(registration) or registration.event_id.mode == 'demand'
class WebsiteDemand(WebsiteEventController):

    # 需求 主頁

    def sitemap_demands(env, rule, qs):
        if not qs or qs.lower() in '/demand':
            yield {'loc': '/demand'}

    def _demands_domain_search(self):
        website = request.website
        return {
            'website_specific': website.website_domain(),
            'invisible': [('is_frontend_invisible', '=', False)],
            'mode':[("mode", "=", 'demand')]
        }

    @http.route(['/demand', '/demand/page/<int:page>', '/demands', '/demands/page/<int:page>'], type='http', auth="public", website=True, sitemap=sitemap_demands)
    def demands(self, page=1, **searches):
        # 先沿用event的code 暫時沒處理不需要的資料
        Event = request.env['event.event']
        SudoEventType = request.env['event.type'].sudo()

        searches.setdefault('search', '')
        searches.setdefault('date', 'all')
        searches.setdefault('tags', '')
        searches.setdefault('type', 'all')
        searches.setdefault('country', 'all')

        website = request.website
        today = fields.Datetime.today()

        def sdn(date):
            return fields.Datetime.to_string(date.replace(hour=23, minute=59, second=59))

        def sd(date):
            return fields.Datetime.to_string(date)

        def get_month_filter_domain(filter_name, months_delta):
            first_day_of_the_month = today.replace(day=1)
            filter_string = _('This month') if months_delta == 0 \
                else format_date(request.env, value=today + relativedelta(months=months_delta),
                                 date_format='LLLL', lang_code=get_lang(request.env).code).capitalize()
            return [filter_name, filter_string, [
                ("date_end", ">=", sd(first_day_of_the_month + relativedelta(months=months_delta))),
                ("date_begin", "<", sd(first_day_of_the_month + relativedelta(months=months_delta+1)))],
                0]

        dates = [
            ['all', _('Upcoming Events'), [("date_end", ">", sd(today))], 0],
            ['today', _('Today'), [
                ("date_end", ">", sd(today)),
                ("date_begin", "<", sdn(today))],
                0],
            get_month_filter_domain('month', 0),
            ['old', _('Past Events'), [
                ("date_end", "<", sd(today))],
                0],
        ]

        # search domains
        domain_search = self._demands_domain_search()

        if searches['search']:
            domain_search['search'] = [('name', 'ilike', searches['search'])]

        search_tags = self._extract_searched_event_tags(searches)
        if search_tags:
            grouped_tags = defaultdict(list)
            for tag in search_tags:
                grouped_tags[tag.category_id].append(tag)
            domain_search['tags'] = []
            for group in grouped_tags:
                domain_search['tags'] = expression.AND([domain_search['tags'], [('tag_ids', 'in', [tag.id for tag in grouped_tags[group]])]])

        current_date = None
        current_type = None
        current_country = None
        if searches["type"] != 'all':
            current_type = SudoEventType.browse(int(searches['type']))
            domain_search["type"] = [("event_type_id", "=", int(searches["type"]))]

        if searches["country"] != 'all' and searches["country"] != 'online':
            current_country = request.env['res.country'].browse(int(searches['country']))
            domain_search["country"] = ['|', ("country_id", "=", int(searches["country"])), ("country_id", "=", False)]
        elif searches["country"] == 'online':
            domain_search["country"] = [("country_id", "=", False)]

        def dom_without(without):
            domain = []
            for key, search in domain_search.items():
                if key != without:
                    domain += search
            return domain

        # count by domains without self search
        for date in dates:
            if date[0] != 'old':
                date[3] = Event.search_count(dom_without('date') + date[2])

        domain = dom_without('type')

        domain = dom_without('country')
        countries = Event.read_group(domain, ["id", "country_id"], groupby="country_id", orderby="country_id")
        countries.insert(0, {
            'country_id_count': sum([int(country['country_id_count']) for country in countries]),
            'country_id': ("all", _("All Countries"))
        })

        order = 'date_begin desc'
        if searches.get('date', 'all') == 'old':
            order = 'date_begin desc'
        order = 'is_published desc, ' + order

        cancelled_stage = request.env['event.stage'].with_context(lang='en_US').search([('name', '=', 'Cancelled')])
        domain_search['cancelled'] = [('stage_id.id', '!=', cancelled_stage.id)]
        now = fields.Datetime.now()
        events = Event.search(dom_without("none"), order=order)
        ongoing_event = events.filtered(lambda self: self.is_published and self.date_end > now)
        events = ongoing_event + (events - ongoing_event)

        keep = QueryURL('/demand', **{key: value for key, value in searches.items() if (key == 'search' or value != 'all')})

        step = 12
        pager = website.pager(
            url="/demand",
            url_args=searches,
            total=len(events),
            page=page,
            step=step,
            scope=5)
        offset = pager['offset']
        events = events[offset: offset + step]

        values = {
            'current_date': current_date,
            'current_country': current_country,
            'current_type': current_type,
            'event_ids': events,  # event_ids used in website_event_track so we keep name as it is
            'dates': dates,
            'categories': request.env['event.tag.category'].search([('mode', '=', 'demand')]),
            'countries': countries,
            'pager': pager,
            'searches': searches,
            'search_tags': search_tags,
            'keep': keep,
        }

        if searches['date'] == 'old':
            # the only way to display this content is to set date=old so it must be canonical
            values['canonical_params'] = OrderedMultiDict([('date', 'old')])

        return request.render("dobtor_demand.index", values)

    # demand 內頁

    def _prepare_demand_values(self, demand, **post):
        """Return the require values to render the template."""
        url = demand._get_event_resource_urls()
        referrer_str = '?referrer=%s' % (request.env.user.partner_id.referral_key)
        demand_url = urls.url_join(request.httprequest.base_url, _build_url_w_params("/demand/%s" % slug(demand), request.params))
        referral_url = urls.url_join(demand_url, referrer_str)
        referral_key = request.httprequest.args.get('referrer', False)
        if referral_key:
            request.session['referral_key'] = referral_key
        return {
            'event': demand,
            'main_object': demand,
            'range': range,
            'google_url': url.get('google_url'),
            'iCal_url': url.get('iCal_url'),
            'referral_url': referral_url,
            'parse_url':urlparse.quote(referral_url)
        }
    

    @http.route(['''/demand/<model("event.event"):demand>'''], type='http', auth="public", website=True, sitemap=False)
    def demand_content(self, demand, **post):
        if request.httprequest.method == 'POST' and request.website.is_public_user():
            return request.redirect("/web/login?redirect=%s" %("/demand/" + slug(demand)))
        if not demand.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()
        values = self._prepare_demand_values(demand, **post)
        demand_sudo = demand.sudo()
        values.update({
            'is_public_user': request.website.is_public_user(),
            'is_close': request.env['event.demand'].sudo().search([('event_id' , '=', demand_sudo.id)], limit=1).state == 'closed'
        })

        return request.render("dobtor_demand.demand_detail_view", values)

    @http.route(['/demand/<model("event.event"):demand>/registration/new'], type='json', auth="public", methods=['POST'], website=True)
    def demand_register_new(self, demand, **post):
        if not demand.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()
        availability_check = False  if demand.seats_limited and demand.seats_available < 1 else True
        values={
            'ticket': demand.event_ticket_ids[:1], 
            'demand': demand, 
            'availability_check': availability_check,
        }
        return request.env['ir.ui.view']._render_template("dobtor_demand.demand_register_details", values)

    @http.route(['/demand/<model("event.event"):demand>/confirm'], type='json', auth="public", methods=['POST'], website=True)
    def demand_confirm(self, demand, **post):
        request_qty = post.pop('request_qty', 1)
        if not demand.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()
        Purchase = request.env['purchase.order'].sudo()
        purchase_val = {'partner_id': request.env.user.partner_id.id}
        website = request.env['website'].get_current_website()
        if len(website.currency_id) != 0:
            purchase_val.update({'currency_id': website.currency_id.id})
        order = Purchase.create(purchase_val)
        order.order_line.unlink()
        po_line = order.order_line.create({
            'name':demand.event_ticket_ids[0].name,
            'product_qty':1,
            'order_id':order.id,
            'price_unit':demand.event_ticket_ids[0].price,
            'product_id':demand.event_ticket_ids[0].product_id.id,
            'product_uom':demand.event_ticket_ids[0].product_id.uom_id.id,
            'date_planned':demand.date_end,
            'event_id':demand.id,
            'event_ticket_id':demand.event_ticket_ids[0].id,
            'taxes_id':False,
            'request_qty': request_qty,
        })
        if po_line:
            po_line._product_id_change()
            po_line._onchange_quantity()
        registrations = self._process_attendees_form(demand, post)
        # 這邊要先移除 event_ticket_id 最後在加回去
        event_ticket_id = demand.event_ticket_ids[0].id
        for registration in registrations:
            if registration.get('event_ticket_id', False):
                registration.pop('event_ticket_id')
        attendees_sudo = self._create_attendees_from_registration_post(demand, registrations)
        attendees_sudo._onchange_partner_id()
        if attendees_sudo:
            attendees_sudo.update({
                'demand_po_id':order.id,
                'demand_po_line_id':po_line.id,
                'request_qty': request_qty, 
                'event_ticket_id': event_ticket_id
            })
        return request.env['ir.ui.view']._render_template("dobtor_demand.demand_register_confirm", {})

    # 修正購物車返回或是其他路由連回去
    @http.route()
    def event_register(self, event, **post):
        if event.mode =='demand':
            return request.redirect("/demand/%s" % slug(event))
        return super().event_register(event,**post)

    @http.route('/my/demand', type='http', auth="user", website=True)
    def my_demand(self, **post):
        partner = request.env.user.partner_id
        
        demands = request.env['event.demand'].sudo().search([
            ('mode', '=', 'demand'),
            ('event_creator_partner', '=', partner.id),
        ])

        values = {
            'partner': partner,
            'demands': demands,
            'position': 'my_demand',            
        }
        return request.render("dobtor_demand.my_demand", values)

class Home(Home):

    @http.route()
    def web_login(self, redirect=None, **kw):
        if redirect and '/demand/' in redirect:
            request.session['auto_popup'] = True
            return request.redirect(redirect)
        return super().web_login(redirect)

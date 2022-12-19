odoo.define('dobtor_demand_marketplace.team_demand_option', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var demand_option = require('dobtor_demand.demand_option');
    var demand_portal_edit = require('dobtor_demand_marketplace.demand_portal_edit');
    var _t = core._t;


    demand_option.DemandOptions.include({
        events: _.extend({}, demand_option.DemandOptions.prototype.events || {}, {
            "click .re_edit": "_onReEditClick",
        }),

        _onReEditClick: function (ev) {
            var $target = $(ev.currentTarget);
            var data = $target.closest('.demand_record__header_operate_wrapper').data();
            var destory_target = $('a.re_edit, a.closed, a.give_up');
            $.extend(data, {
                'is_team': true,
                'destory_target': destory_target,
                're_edit': true,
            });
            destory_target.css('pointer-events', 'none');
            destory_target.css('opacity', 0.65);

            return new demand_portal_edit.DemandPortalEditDialog(this, data).open();
        },
    });

    publicWidget.registry.TeamDemandOptions = publicWidget.Widget.extend({
        selector: '.demand_record__header_operate_wrapper',
        events: {
            'click .open': '_onApproveClick',
            'click .cancel': '_onRejectClick',
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        _onApproveClick: function (ev) {
            var $target = $(ev.currentTarget);
            var demand_id = $target.closest('.demand_record__header_operate_wrapper').data('demand_id');
            $('a.open, a.cancel').css('pointer-events', 'none');
            $('a.open, a.cancel').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/option',
                params: {'approve': true, 'demand_id': demand_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onRejectClick: function (ev) {
            var $target = $(ev.currentTarget);
            var demand_id = $target.closest('.demand_record__header_operate_wrapper').data('demand_id');
            $('a.open, a.cancel').css('pointer-events', 'none');
            $('a.open, a.cancel').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/option',
                params: {'reject': true, 'demand_id': demand_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },
    });

    publicWidget.registry.TeamDemandBodyOptions = publicWidget.Widget.extend({
        selector: '.demand_record__body_operate_wrapper',
        events: {
            'click .open': '_onApproveClick',
            'click .cancel': '_onRejectClick',
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        _onApproveClick: function (ev) {
            var $target = $(ev.currentTarget);
            var registration_id = $target.data('registration_id');
            $('a.open, a.cancel').css('pointer-events', 'none');
            $('a.open, a.cancel').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/body_option',
                params: {'approve': true, 'registration_id': registration_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onRejectClick: function (ev) {
            var $target = $(ev.currentTarget);
            var registration_id = $target.data('registration_id');
            $('a.open, a.cancel').css('pointer-events', 'none');
            $('a.open, a.cancel').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/body_option',
                params: {'reject': true, 'registration_id': registration_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },
    });

    publicWidget.registry.TeamDemandCreatorCheckOptions = publicWidget.Widget.extend({
        selector: '.demand_record__creator_check_operate_wrapper',
        events: {
            'click .open': '_onApproveClick',
            'click .appeal': '_onAppealClick',
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        _onApproveClick: function (ev) {
            var $target = $(ev.currentTarget);
            var registration_id = $target.data('registration_id');
            $('a.open, a.cancel, a.appeal').css('pointer-events', 'none');
            $('a.open, a.cancel, a.appeal').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/creator_check_option',
                params: {'approve': true, 'registration_id': registration_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onAppealClick: function (ev) {
            var $target = $(ev.currentTarget);
            var registration_id = $target.data('registration_id');
            $('a.open, a.cancel, a.appeal').css('pointer-events', 'none');
            $('a.open, a.cancel, a.appeal').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/creator_check_option',
                params: {'appeal': true, 'registration_id': registration_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },
    });

    publicWidget.registry.TeamDemandServiceAuditOptions = publicWidget.Widget.extend({
        selector: '.service_audit__header_operate_wrapper',
        events: {
            'click .open': '_onApproveClick',
            'click .cancel': '_onRejectClick',
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        _onApproveClick: function (ev) {
            var $target = $(ev.currentTarget);
            var registration_id = $target.data('registration_id');
            $('a.open, a.cancel').css('pointer-events', 'none');
            $('a.open, a.cancel').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/service_audit_option',
                params: {'approve': true, 'registration_id': registration_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onRejectClick: function (ev) {
            var $target = $(ev.currentTarget);
            var registration_id = $target.data('registration_id');
            $('a.open, a.cancel').css('pointer-events', 'none');
            $('a.open, a.cancel').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/service_audit_option',
                params: {'reject': true, 'registration_id': registration_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },
    });

    publicWidget.registry.TeamDemandServiceOptions = publicWidget.Widget.extend({
        selector: '.service_record__header_operate_wrapper',
        events: {
            'click .open': '_onApproveClick',
            'click .cancel': '_onCancelClick',
            'click .appeal': '_onAppealClick',
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        _onApproveClick: function (ev) {
            var $target = $(ev.currentTarget);
            var registration_id = $target.closest('.service_record__header_operate_wrapper').data('registration_id');
            $('a.open, a.cancel, a.appeal').css('pointer-events', 'none');
            $('a.open, a.cancel, a.appeal').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/service_option',
                params: {'approve': true, 'registration_id': registration_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onCancelClick: function (ev) {
            var $target = $(ev.currentTarget);
            var registration_id = $target.closest('.service_record__header_operate_wrapper').data('registration_id');
            $('a.open, a.cancel, a.appeal').css('pointer-events', 'none');
            $('a.open, a.cancel, a.appeal').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/service_option',
                params: {'cancel': true, 'registration_id': registration_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onAppealClick: function (ev) {
            var $target = $(ev.currentTarget);
            var registration_id = $target.closest('.service_record__header_operate_wrapper').data('registration_id');
            $('a.open, a.cancel, a.appeal').css('pointer-events', 'none');
            $('a.open, a.cancel, a.appeal').css('opacity', 0.65);

            return this._rpc({
                route: '/team_demand/service_option',
                params: {'appeal': true, 'registration_id': registration_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },
    });

    return  {
        TeamDemandOptions: publicWidget.registry.TeamDemandOptions,
        TeamDemandBodyOptions: publicWidget.registry.TeamDemandBodyOptions,
        TeamDemandCreatorCheckOptions: publicWidget.registry.TeamDemandCreatorCheckOptions,
        TeamDemandServiceAuditOptions: publicWidget.registry.TeamDemandServiceAuditOptions,
        TeamDemandServiceOptions: publicWidget.registry.TeamDemandServiceOptions,
    };
});
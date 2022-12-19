odoo.define('dobtor_demand_application.demand_reject_application', function (require) {
    'use strict';

    const core = require('web.core');
    const request_common = require('dobtor_request_application.request_common');
    const demand_option = require('dobtor_demand_marketplace.team_demand_option');
    const _t = core._t;

    demand_option.TeamDemandOptions.include({
        xmlDependencies: (demand_option.TeamDemandOptions.prototype.xmlDependencies || []).concat(
            ['/dobtor_demand_application/static/src/xml/demand_reject_modal.xml']
        ),
        _openDemandRejectDialog: function ($element) {
            let data = $element.data();
            data = _.extend({}, data, {
                'reject' : true,
                'demand_id' : $element.closest('.demand_record__header_operate_wrapper').data('demand_id'),
                'template': 'dobtor.demand.reject.modal',
                'route': '/team_demand/option',
                'title': _t("Demand Reject"),
            });
            return new request_common.requestDialog(this, data).open();
        },
        _onRejectClick: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            let $target = $(ev.currentTarget);
            let self = this;
            this._rpc({
                model: 'request.action',
                method: 'get_active',
                args: ['dobtor_demand_application.action_demand_reject'],
            }).then(function (result) {
                if (result)
                    self._openDemandRejectDialog($target);
                else {
                    self._rpc({
                        route: '/team_demand/option',
                        params: {'reject': true, 'demand_id': $target.closest('.demand_record__header_operate_wrapper').data('demand_id'),},
                    }).then(function (result) {
                        if (result)
                            window.location.reload();
                    });
                }
            });
        },
    });

    demand_option.TeamDemandServiceAuditOptions.include({
        xmlDependencies: (demand_option.TeamDemandServiceAuditOptions.prototype.xmlDependencies || []).concat(
            ['/dobtor_demand_application/static/src/xml/service_reject_modal.xml']
        ),
        _openServiceRejectDialog: function ($element) {
            let data = $element.data();
            data = _.extend({}, data, {
                'reject' : true,
                'registration_id' : $element.data('registration_id'),
                'template': 'dobtor.service.reject.modal',
                'route': '/team_demand/service_audit_option',
                'title': _t("Service Reject"),
            });
            return new request_common.requestDialog(this, data).open();
        },
        _onRejectClick: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            let $target = $(ev.currentTarget);
            let self = this;
            this._rpc({
                model: 'request.action',
                method: 'get_active',
                args: ['dobtor_demand_application.action_service_reject'],
            }).then(function (result) {
                if (result)
                    self._openServiceRejectDialog($target);
                else {
                    self._rpc({
                        route: '/team_demand/service_audit_option',
                        params: {'reject': true, 'registration_id': $target.data('registration_id'),},
                    }).then(function (result) {
                        if (result)
                            window.location.reload();
                    });
                }   
            });

        },
    });

    demand_option.TeamDemandBodyOptions.include({
        xmlDependencies: (demand_option.TeamDemandBodyOptions.prototype.xmlDependencies || []).concat(
            ['/dobtor_demand_application/static/src/xml/service_creator_reject_modal.xml']
        ),
        _openServiceRejectDialog: function ($element) {
            let data = $element.data();
            data = _.extend({}, data, {
                'reject' : true,
                'registration_id' : $element.data('registration_id'),
                'template': 'dobtor.service.creator.reject.modal',
                'route': '/team_demand/body_option',
                'title': _t("Service Reject"),
            });
            return new request_common.requestDialog(this, data).open();
        },
        _onRejectClick: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            let $target = $(ev.currentTarget);
            let self = this;
            this._rpc({
                model: 'request.action',
                method: 'get_active',
                args: ['dobtor_demand_application.action_creator_service_reject'],
            }).then(function (result) {
                if (result)
                    self._openServiceRejectDialog($target);
                else {
                    self._rpc({
                        route: '/team_demand/body_option',
                        params: {'reject': true, 'registration_id': $target.data('registration_id'),},
                    }).then(function (result) {
                        if (result)
                            window.location.reload();
                    });
                }   
            });

        },
    });
});
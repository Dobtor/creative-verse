odoo.define('dobtor_demand_application.demand_appeal_application', function (require) {
    'use strict';

    const core = require('web.core');
    const request_common = require('dobtor_request_application.request_common');
    const demand_option = require('dobtor_demand_marketplace.team_demand_option');
    const _t = core._t;

    demand_option.TeamDemandCreatorCheckOptions.include({
        xmlDependencies: (demand_option.TeamDemandCreatorCheckOptions.prototype.xmlDependencies || []).concat(
            ['/dobtor_demand_application/static/src/xml/service_appeal_modal.xml']
        ),
        _openServiceAppealDialog: function ($element) {
            let data = $element.data();
            data = _.extend({}, data, {
                'appeal' : true,
                'registration_id' : $element.data('registration_id'),
                'template': 'dobtor.service.appeal.modal',
                'route': '/team_demand/creator_check_option',
                'title': _t("Service Appeals"),
            });
            return new request_common.requestDialog(this, data).open();
        },
        _onAppealClick: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            let $target = $(ev.currentTarget);
            let self = this;
            this._rpc({
                model: 'request.action',
                method: 'get_active',
                args: ['dobtor_demand_application.action_creator_appeal_reject'],
            }).then(function (result) {
                if (result)
                    self._openServiceAppealDialog($target);
                else {
                    self._rpc({
                        route: '/team_demand/creator_check_option',
                        params: {'appeal': true, 'registration_id': $target.data('registration_id'),},
                    }).then(function (result) {
                        if (result)
                            window.location.reload();
                    });
                }   
            });

        },
    });


    demand_option.TeamDemandServiceOptions.include({
        xmlDependencies: (demand_option.TeamDemandServiceOptions.prototype.xmlDependencies || []).concat(
            ['/dobtor_demand_application/static/src/xml/service_appeal_modal.xml']
        ),
        _openServiceAppealDialog: function ($element) {
            let data = $element.data();
            data = _.extend({}, data, {
                'appeal' : true,
                'registration_id' : $element.closest('.service_record__header_operate_wrapper').data('registration_id'),
                'template': 'dobtor.service.appeal.modal',
                'route': '/team_demand/service_option',
                'title': _t("Service Appeal"),
            });
            return new request_common.requestDialog(this, data).open();
        },
        _onAppealClick: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            let $target = $(ev.currentTarget);
            let self = this;
            this._rpc({
                model: 'request.action',
                method: 'get_active',
                args: ['dobtor_demand_application.action_attendee_appeal_reject'],
            }).then(function (result) {
                if (result)
                    self._openServiceAppealDialog($target);
                else {
                    self._rpc({
                        route: '/team_demand/service_option',
                        params: {'appeal': true, 'registration_id': $target.closest('.service_record__header_operate_wrapper').data('registration_id'),},
                    }).then(function (result) {
                        if (result)
                            window.location.reload();
                    });
                }   
            });

        },
    });
});
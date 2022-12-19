odoo.define('dobtor_demand_application.demand_give_up_application', function (require) {
    'use strict';

    const core = require('web.core');
    const request_common = require('dobtor_request_application.request_common');
    const demand_option = require('dobtor_demand.demand_option');
    const _t = core._t;

    demand_option.DemandOptions.include({
        xmlDependencies: (demand_option.DemandOptions.prototype.xmlDependencies || []).concat(
            ['/dobtor_demand_application/static/src/xml/demand_give_up_modal.xml']
        ),
        _openGiveUpDialog: function ($element) {
            let data = $element.data();
            data = _.extend({}, data, {
                'give_up' : true,
                'demand_id' : $element.closest('.demand_record__header_operate_wrapper').data('demand_id'),
                'template': 'dobtor.demand.give_up.modal',
                'route': '/demand/option',
                'title': _t("Demand GiveUp"),
            });
            return new request_common.requestDialog(this, data).open();
        },

        _onGiveUpClick: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            let $target = $(ev.currentTarget);
            let self = this;
            this._rpc({
                model: 'request.action',
                method: 'get_active',
                args: ['dobtor_demand_application.action_demand_give_up'],
            }).then(function (result) {
                if (result)
                    self._openGiveUpDialog($target);
                else {
                    self._rpc({
                        route: '/demand/option',
                        params: {'give_up': true, 'demand_id': $target.closest('.demand_record__header_operate_wrapper').data('demand_id'),},
                    }).then(function (result) {
                        if (result)
                            window.location.reload();
                    });
                }  
            });
            
        },
    });
});
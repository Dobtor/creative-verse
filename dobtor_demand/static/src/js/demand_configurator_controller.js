odoo.define('dobtor_demand.DemandConfiguratorFormController', function (require) {
    "use strict";

    var FormController = require('web.FormController');

    var DemandConfiguratorFormController = FormController.extend({

        saveRecord: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var state = self.renderer.state.data;
                self.do_action({type: 'ir.actions.act_window_close', infos: {
                    eventConfiguration: {
                        event_id: {id: state.event_id.data.id},
                        event_ticket_id: {id: state.event_ticket_id.data.id}
                    }
                }});
            });
        }
    });

    return DemandConfiguratorFormController;

});
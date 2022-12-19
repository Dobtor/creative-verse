odoo.define('dobtor_demand.DemandConfiguratorFormView', function (require) {
    "use strict";

    var DemandConfiguratorFormController = require('dobtor_demand.DemandConfiguratorFormController');
    var FormView = require('web.FormView');
    var viewRegistry = require('web.view_registry');


    var DemandConfiguratorFormController = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: DemandConfiguratorFormController
        }),
    });

    viewRegistry.add('event_configurator_form', DemandConfiguratorFormController);

    return DemandConfiguratorFormController;

});
odoo.define('dobtor_demand.product_demand_configurator', function (require) {

    var relationalFields = require('web.relational_fields');
    var FieldsRegistry = require('web.field_registry');
    var core = require('web.core');
    var _t = core._t;


    var DemandConfiguratorWidget = relationalFields.FieldMany2One.extend({
        events: _.extend({}, relationalFields.FieldMany2One.prototype.events, {
            'click .o_edit_product_configuration': '_onEditProductConfiguration'
        }),

        _addProductLinkButton: function () {
            if (this.$('.o_external_button').length === 0) {
                var $productLinkButton = $('<button>', {
                    type: 'button',
                    class: 'fa fa-external-link btn btn-secondary o_external_button',
                    tabindex: '-1',
                    draggable: false,
                    'aria-label': _t('External Link'),
                    title: _t('External Link')
                });

                var $inputDropdown = this.$('.o_input_dropdown');
                $inputDropdown.after($productLinkButton);
            }
         },

        _render: function () {
           this._super.apply(this, arguments);
           if (this.mode === 'edit' && this.value &&
           (this._isConfigurableLine())) {
               this._addProductLinkButton();
               this._addConfigurationEditButton();
           } else if (this.mode === 'edit' && this.value) {
               this._addProductLinkButton();
           } else {
               this.$('.o_edit_product_configuration').hide();
           }
        },

        _addConfigurationEditButton: function () {
            var $inputDropdown = this.$('.o_input_dropdown');

            if ($inputDropdown.length !== 0 &&
                this.$('.o_edit_product_configuration').length === 0) {
                var $editConfigurationButton = $('<button>', {
                    type: 'button',
                    class: 'fa fa-pencil btn btn-secondary o_edit_product_configuration',
                    tabindex: '-1',
                    draggable: false,
                    'aria-label': _t('Edit Configuration'),
                    title: _t('Edit Configuration')
                });

                $inputDropdown.after($editConfigurationButton);
            }
         },

        _onProductChange: function (productId, dataPointId) {
            var self = this;
            return self._checkForEvent(productId, dataPointId);
          },

        reset: async function (record, ev) {
            await this._super(...arguments);
            if (ev && ev.target === this) {
                if (ev.data.changes && !ev.data.preventProductIdCheck && ev.data.changes.product_template_id) {
                    this._onTemplateChange(record.data.product_template_id.data.id, ev.data.dataPointID);
                } else if (ev.data.changes && ev.data.changes.product_id) {
                    this._onProductChange(record.data.product_id.data && record.data.product_id.data.id, ev.data.dataPointID).then(wizardOpened => {
                        if (!wizardOpened) {
                            this._onLineConfigured();
                        }
                    });
                }
            }
        },

        _onLineConfigured: function () {

        },

        _isConfigurableLine: function () {
            return this.recordData.event_ok ;
        },

        _checkForEvent: function (productId, dataPointId) {
            var self = this;
            return this._rpc({
                model: 'product.product',
                method: 'read',
                args: [productId, ['event_ok']],
            }).then(function (result) {
                if (result && result[0].event_ok) {
                    self._openEventConfigurator({
                            default_product_id: productId
                        },
                        dataPointId
                    );
                    return Promise.resolve(true);
                }
                return Promise.resolve(false);
            });
        },


        _onEditConfiguration: function () {
            if (this._isConfigurableLine()) {
                this._onEditLineConfiguration();
            } else if (this._isConfigurableProduct()) {
                this._onEditProductConfiguration();
            }
        },

        _onEditLineConfiguration: function () {
            if (this.recordData.event_ok) {
                var defaultValues = {
                    default_product_id: this.recordData.product_id.data.id
                };

                if (this.recordData.event_id) {
                    defaultValues.default_event_id = this.recordData.event_id.data.id;
                }

                if (this.recordData.event_ticket_id) {
                    defaultValues.default_event_ticket_id = this.recordData.event_ticket_id.data.id;
                }

                this._openEventConfigurator(defaultValues, this.dataPointID);
            } else {
                this._super.apply(this, arguments);
            }
        },


        _onTemplateChange: function (productTemplateId, dataPointId) {
            return Promise.resolve(false);
        },

        _onEditProductConfiguration: function () {

        },

        _openEventConfigurator: function (data, dataPointId) {
            var self = this;
            this.do_action('dobtor_demand.demand_configurator_action', {
                additional_context: data,
                on_close: function (result) {
                    if (result && !result.special) {
                        self.trigger_up('field_changed', {
                            dataPointID: dataPointId,
                            changes: result.eventConfiguration,
                            onSuccess: function () {
                                self._onLineConfigured();
                            }
                        });
                    } else {
                        if (!self.recordData.event_id || !self.recordData.event_ticket_id) {
                            self.trigger_up('field_changed', {
                                dataPointID: dataPointId,
                                changes: {
                                    product_id: false,
                                    name: ''
                                },
                            });
                        }
                    }
                }
            });
        }
    });

    FieldsRegistry.add('demand_configurator', DemandConfiguratorWidget);

    return DemandConfiguratorWidget;

    });
odoo.define('dobtor_demand_marketplace.demand_portal_edit', function (require) {
    "use strict";

    const core = require('web.core');
    var publicWidget = require('web.public.widget');
    var demand_portal_upload = require('dobtor_demand_marketplace.demand_portal_upload');
    var time = require('web.time');
    var utils = require('web.utils');
    const ajax = require('web.ajax');
    const _t = core._t;

    var DemandPortalEditDialog = demand_portal_upload.DemandPortalUploadDialog.extend({
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.demand_id = options.demand_id == undefined ? false : options.demand_id;
            this.destory_target = options.destory_target || false;
            this.re_edit = options.re_edit || false;
        },
        willStart: function () {
            var defs = [this._super.apply(this, arguments)];
            var self = this;

            defs.push(this._rpc({
                model: 'event.demand',
                method: 'get_demand_edit_data',
                args: [this.demand_id],
            }).then(function (result) {
                self.old_values = result;
            }));

            return Promise.all(defs);
        },
        start: function () {
            var defs = [this._super.apply(this, arguments)];

            // #region: 需求時間預設值
            var default_event_start_date = moment(time.str_to_datetime(this.old_values.date_begin)).format('YYYY-MM-DD');
            var default_event_end_date = moment(time.str_to_datetime(this.old_values.date_end)).format('YYYY-MM-DD');
            var default_event_start_time = moment(time.str_to_datetime(this.old_values.date_begin)).format('HH:mm');
            var default_event_end_time = moment(time.str_to_datetime(this.old_values.date_end)).format('HH:mm');

            this.$('#event_date #event_jq_date input.date.start').datepicker('setDate', default_event_start_date);
            this.$('#event_date #event_jq_date input.date.end').datepicker('setDate', default_event_end_date);
            if (!(default_event_start_time == '00:00' && default_event_end_time == '23:59')) {
                this.$('#all_day_event_date').click().change();
                this.$('#event_date #event_jq_date input.time.start').timepicker('setTime', default_event_start_time);
                this.$('#event_date #event_jq_date input.time.end').timepicker('setTime', default_event_end_time);
            }
            // #endregion
            
            // #region: 需求地點預設值
            if (!this.old_values.event_address_disabled) {
                this.$('#event_address_show').click().change();
                if (this.old_values.online_address) {
                    this.$('input[name="online_address_option"]').click().change();
                    this.$('#event_address').val(this.old_values.event_address);
                }
    
                if (this.old_values.offline_address) {
                    this.$('input[name="offline_address_option"]').click().change();
                    this.$('#city').val(this.old_values.city);
                    this.$('#zip').val(this.old_values.zip);
                    this.$('#street').val(this.old_values.street);
                }
            }
            // #endregion

            // #region: 需求描述預設值
            this.$('#description').val(this.old_values.description);
            // #endregion

            // #region: 需求票種預設值
            if (this.old_values.event_ticket_ids.length) {
                if (this.old_values.event_ticket_ids[0]['pricing_method'] != 'times') {
                    this.$('#select_unit').val(this.old_values.event_ticket_ids[0]['pricing_method']);
                    this.$('#min_request_unit').val(this.old_values.event_ticket_ids[0]['min_request_unit']);
                    this.$('#pricing_method_hours').click().change();
                } else {
                    this.$('#price').val(this.old_values.event_ticket_ids[0]['price']);
                }
                this.$('#request_qty').val(this.old_values.event_ticket_ids[0]['request_qty']);
            }
            // #endregion

            return Promise.all(defs);
        },

        _bindSelect2Dropdown: function () {
            this._super.apply(this, arguments);
            if (this.old_values['organizer_id'].length) {
                this.$('#organizer_id').val(JSON.stringify(this.old_values['organizer_id'])).trigger('change');
            }
            if (this.old_values['tag_ids'].length) {
                this.$('#tag_ids').val(JSON.stringify(this.old_values['tag_ids'])).trigger('change');
            }
            if (!this.old_values.event_address_disabled && this.old_values.offline_address && this.old_values.state_id) {
                this.$('#state_id').val(JSON.stringify(this.old_values.state_id)).trigger('change');
            }
        },

        _getSelect2DropdownValues: function () {
            var result = this._super.apply(this, arguments);
            var newTag = [];

            _.each(this.$('#tag_ids').select2('data'), function (val) {
                if (!val.create)
                    newTag.push(val.id);
            });
            // --------edit remove tag-------
            _.each(this.old_values['tag_ids'], function (old) {
                if (newTag.includes(old.id) === false) 
                    result['tag_ids'].push([3, old.id]);
            });
            //--------------------------------

            return result;
        },

        _onClickFormSubmit: function (ev) {
            var self = this;
            
            if (this._formValidate()) {
                if (this._wysiwyg) {
                    this._wysiwyg.save();
                }
                var values = this._formValidateGetValues();
                $.extend(values, {
                    'demand_id': this.demand_id,
                    're_edit': this.re_edit,
                });
                return this._rpc({
                    route: '/demand/edit_demand',
                    params: values,
                }).then(function (data) {
                    self._onFormSubmitDone(data);
                });
            }
        },

        destroy: function () {
            if (this.destory_target){
                this.destory_target.css('pointer-events', 'unset');
                this.destory_target.css('opacity', 'unset');
            }
            this._super();
        },
    });

    return {
        DemandPortalEditDialog: DemandPortalEditDialog,
    };
});
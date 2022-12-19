odoo.define('dobtor_demand_marketplace.demand_portal_upload', function (require) {
    "use strict";

    const core = require('web.core');
    var Dialog = require('web.Dialog');
    var time = require('web.time');
    var publicWidget = require('web.public.widget');
    var wysiwygLoader = require('web_editor.loader');
    var utils = require('web.utils');
    const ajax = require('web.ajax');
    const _t = core._t;

    var DemandPortalUploadDialog = Dialog.extend({
        template: 'website.demand.portal.upload.modal',
        events: _.extend({}, Dialog.prototype.events, {
            'click .upload_icon': '_onClickUploadIcon',
            'change input#upload': '_onChangeEventUpload',
            'change #all_day_event_date': '_onEventAlldayChanged',
            'change input[name="pricing_method"]': '_onTicketPricingMethodPChanged',
            'change #min_request_unit': '_onEventrequestNuitChange',
            'change #select_unit': '_onEventrequestNuitChange',
            'change input[name="event_address_option"]': '_onAddressChanged',
            'change input[name="online_address_option"]': '_onOnlineAddressOptionChanged',
            'change input[name="offline_address_option"]': '_onOfflineAddressOptionChanged',
        }),
        is_team: false,
        init: function (parent, options) {
            var buttons = [{
                    text: _t("Submit review"),
                    classes: 'demand_submit ml-auto bg-o-color-1',
                    click: this._onClickFormSubmit.bind(this)
                },
                {
                    text: _t("Re-edit"),
                    classes: 'demand_re_edit bg-o-color-1 d-none',
                    click: this._onClickReEdit.bind(this)
                },
            ];
            this._super(parent, _.extend({}, {
                title: _t("Upload Demand"),
                size: 'medium',
                dialogClass: 'event_upload_body',
                buttons: buttons,
            }, options || {}));
            this.is_team = options.is_team == undefined ? false : options.is_team;
            this.file = {};
        },
        start: function () {
            this.$modal.find(".modal-header").addClass('event_upload_header');
            this.$footer.addClass('event_upload_footer');
            this.$footer.prepend('<div class="d-flex flex-column footer_error_msg w-100 mb-3"/>');
            this.$chargeableInput = this.$('#chargeable');
            this.$registeroptionInput = this.$('#register_option');
            this.$offlineInput = this.$('#offline');
            this.$behalfregisterInput = this.$('#behalf_register');

            this.$('#event_jq_date .time').timepicker({
                'showDuration': true,
                'timeFormat': 'H:i'
            });
        
            this.$('#event_jq_date .date').datepicker({
                'format': 'yyyy-mm-dd',
                'autoclose': true,
                'todayHighlight' : true,

            });
            this.$('#event_jq_date').datepair();

            this._bindSelect2Dropdown();

            var toolbar = [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'clear']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['insert', ['link']],
                ['history', ['undo', 'redo']],
            ];
            
            var $textarea = this.$('textarea.o_wysiwyg_loader');
            wysiwygLoader.load(this, $textarea[0], {
                toolbar: toolbar,
                styleWithSpan: false,
                disableResizeImage: true,
            }).then(wysiwyg => {
                this._wysiwyg = wysiwyg;
            });
        },

        _bindSelect2Dropdown: function () {
            var self = this;
            this.$('#tag_ids').select2(this._select2Wrapper(_t('Event Tags'), true, function () {
                return self._rpc({
                    route: '/demand/tag/search_read',
                    params: {
                        fields: ['name'],
                        domain: [['category_id.mode', '=', 'demand']],
                    }
                });
            }));
            // region : 之後如果有要遷移, 該區塊可保留於 dobtor_demand_marketplace 模組
            this.$('#organizer_id').select2(this._select2Wrapper(_t('O'), false,
                function () {
                    return self._rpc({
                        route: '/demand/portal/organizer/search_read',
                        params: {
                            fields: ['name'],
                        }
                    });
                })
            );
            // endregion 
            this.$('#state_id').select2(this._select2Wrapper(_t('Counties'), false,
                function () {
                    return self._rpc({
                        route: '/partner/state/search_read',
                        params: {
                            fields: ['name'],
                            domain: [],
                        }
                    });
                })
            );
        },
        
        _onClickUploadIcon: function (ev) {
            this.$('input#upload').click();
        },

        _onChangeEventUpload: function (ev) {
            var self = this;
            this._alertRemove();
    
            var $input = $(ev.currentTarget);
            var preventOnchange = $input.data('preventOnchange');
            var $preview = self.$('#event-image');
            var $custom_label = self.$('.custom-file-label');
    
            var file = ev.target.files[0];
            if (!file) {
                this.$('#event-image').attr('src', '#');
                return;
            }
            var isImage = /^image\/.*/.test(file.type);
            var loaded = false;
            this.file.name = file.name;
            this.file.type = file.type;
            $custom_label.html(this.file.name.split("\\").pop());
            if (!isImage) {
                this._alertDisplay(_t("Invalid file type. Please select image file"));
                this._fileReset();
                return;
            }
            if (file.size / 1024 / 1024 > 25) {
                this._alertDisplay(_t("File is too big. File size cannot exceed 25MB"));
                this._fileReset();
                return;
            }
    
            utils.getDataURLFromFile(file).then(function (buffer) {
                if (isImage) {
                    $preview.attr('src', buffer);
                }
                buffer = buffer.split(',')[1];
                self.file.data = buffer;
            });
        },

        _fileReset: function () {
            var control = this.$('#upload');
            control.replaceWith(control = control.clone(true));
            this.file.name = false;
        },

        _alertDisplay: function (message) {
            this._alertRemove();
            this.$footer.find('.footer_error_msg').append(
                $('<div/>', {
                    "class": 'alert alert-warning',
                    id: 'upload-alert',
                    role: 'alert'
                }).text(message)
            );
        },
        _alertRemove: function () {
            this.$('#upload-alert').remove();
        },

        _formSetFieldValue: function (fieldId, value) {
            this.$('form').find('#' + fieldId).val(value);
        },
        _formGetFieldValue: function (fieldId) {
            return this.$('#' + fieldId).val();
        },
        _select2Validate: function (target) {
            if (target.length !== 0) {
                var $select2Container = target
                    .siblings('.select2-container');
                $select2Container.removeClass('is-invalid is-valid');
                if (target.is(':invalid')) {
                    $select2Container.addClass('is-invalid');
                } else if (target.is(':valid')) {
                    $select2Container.addClass('is-valid');
                }
            }
        },
        _formValidate: function () {
            var form = this.$("form");
            var invalid_label = [];
            form.addClass('was-validated');
            this.$footer.find('.footer_error_msg').empty();
            this.$('.error_msg').remove();
            // region : 之後如果有要遷移, 該區塊可保留於 dobtor_demand_marketplace 模組
            this._select2Validate(this.$('#organizer_id'));
            // endregion 
            _.each(this.$('input:invalid'), function (obj) {
                invalid_label.push($(obj).closest('.form-group').find('label:first').text());
                if ($(obj).attr('type') == 'text')
                    $(obj).after(
                        $('<span/>', {
                            "class": 'fa fa-exclamation-triangle text-danger error_msg',
                        }).text(_t('input error'))
                    );
            });
            if (invalid_label.length) {
                // filter 排除重複字串
                this.$footer.find('.footer_error_msg').append(
                    $('<span/>', {
                        "class": 'fa fa-exclamation-triangle text-danger',
                    }).text('「' + invalid_label.filter((ele,pos) => invalid_label.indexOf(ele) == pos).join('、') + _t('」 input error'))
                );
            }

            return form[0].checkValidity();
        },

        _mergeDateTime: function (date, time){
            if ((date && time) != ''){
                return date + ' ' + time
            }
            else if (time == ''){
                return date
            }
            else{
                return false
            }
        },
        
        _formValidateGetValues: function (forcePublished) {
            var values = _.extend({
                'name': this._formGetFieldValue('name'),
                'subtitle': this._formGetFieldValue('subtitle'),
                'request_qty': this._formGetFieldValue('request_qty'),
                'min_request_unit': this._formGetFieldValue('min_request_unit'),
                'date_begin': this._parse_date(this._mergeDateTime(this._formGetFieldValue('event_date #event_jq_date .date.start'), this._formGetFieldValue('event_date #event_jq_date .time.start'))),
                'date_end': this._parse_date(this._mergeDateTime(this._formGetFieldValue('event_date #event_jq_date .date.end'), this._formGetFieldValue('event_date #event_jq_date .time.end')), 'end'),
                'price': this._formGetFieldValue('price'),
                'need_register': '1',
                'description': this._formGetFieldValue('description') != '' ? this._formGetFieldValue('description') : ' ',
                'pricing_method': $('#pricing_method_times').is(':checked')? 'times': $('#select_unit').val(),
                // region :之後如果有要遷移, 該區塊可保留於 dobtor_demand_marketplace 模組
                'event_organizer': this._formGetFieldValue('event_organizer'),
                'organizer_id': this.$('#organizer_id').select2('data').id,
                // endregion 
                'n_login_register': false,
                'is_team': this.is_team,
                'is_use_team_wallet': this.$('#is_use_team_wallet').length == 0 ? false : this.$('#is_use_team_wallet').is(':checked'),
                'is_show_public': $('#is_show_public').is(':checked')
            }, this._getSelect2DropdownValues()); 

            // #region : Address disabled/show
            if (this.$("input[name='event_address_option']:checked").attr('id') == 'event_address_no_show') {
                _.extend(values, {
                    'event_address_disabled': true,
                });
            } else if (this.$("input[name='event_address_option']:checked").attr('id') == 'event_address_show') {
                if (this.$('input[name="online_address_option"]').is(':checked')){
                    _.extend(values, {
                        'online_address': true,
                        'event_address': this._formGetFieldValue('event_address'),
                    });
                }
                if (this.$('input[name="offline_address_option"]').is(':checked')){
                    _.extend(values, {
                        'offline_address': true,
                        'state_id': this.$('#state_id').select2('data').id,
                        'city': this._formGetFieldValue('city'),
                        'zip': this._formGetFieldValue('zip'),
                        'street': this._formGetFieldValue('street'),
                    });
                }
            }
            // #endregion

            if (/^image\/.*/.test(this.file.type)) {
                _.extend(values, {
                    'event_default_cover': this.file.data,
                });
            }

            return values;
        },

        _getSelect2DropdownValues: function () {
            var result = {};
            var self = this;
            // tags
            var tagValues = [];
            _.each(this.$('#tag_ids').select2('data'), function (val) {
                if (val.create) {
                    tagValues.push([0, {'name': val.text}]);
                } else {
                    tagValues.push([4, val.id]);
                }
            });
            if (tagValues) {
                result['tag_ids'] = tagValues;
            }

            return result;
        },

        _parse_date: function (value, type) {
            var datetime = moment(value, 'YYYY-MM-DD HH:mm', true);
            var onlydate = moment(value, 'YYYY-MM-DD', true);
            if (datetime.isValid()) {
                return time.datetime_to_str(datetime.toDate());
            } else if (onlydate.isValid()){
                if (type == 'end'){
                    return time.datetime_to_str(onlydate.add(1, 'days').subtract(1, 'seconds').toDate());
                }
                else{
                    return time.datetime_to_str(onlydate.toDate());
                }
            } else {
                return false;
            }
        },

        _onClickFormSubmit: function (ev) {
            var self = this;
            var $btn = $(ev.currentTarget);

            if (this._formValidate()) {
                if (this._wysiwyg) {
                    this._wysiwyg.save();
                }
                var values = this._formValidateGetValues(); // get info before changing state
                return this._rpc({
                    route: '/demand/upload_demand',
                    params: values,
                }).then(function (data) {
                    self._onFormSubmitDone(data);
                });
            }
        },

        _onClickReEdit: function (ev) {
            this.$('#is_use_team_wallet').remove();
            this.$footer.find('.footer_error_msg').empty();
            this.$footer.find('.demand_submit').text(_t('Submit review'));
            this.$footer.find('.demand_re_edit').toggleClass('d-none', true);
            this.$el.css('pointer-events', 'unset');
            this.$el.css('opacity', 'unset');
        },

        _onFormSubmitDone: function (data) {
            if (data.error) {
                this._alertDisplay(data.error);
                this._useTeamWallet(data);
            } else {
                window.location = data.url;
            }
        },

        _useTeamWallet: function(data) {
            if (data.use_team_wallet) {
                this.$footer.find('.demand_submit').text(_t('Team pay'));
                this.$footer.find('.demand_re_edit').toggleClass('d-none', false);
                this.$el.css('pointer-events', 'none');
                this.$el.css('opacity', 0.65);

                if (this.$('#is_use_team_wallet').length == 0) {
                    this.$('form').append($('<input/>', {
                        type: 'radio', 
                        id: 'is_use_team_wallet',
                        class: 'd-none', 
                        checked: 'checked',
                    }));
                }
            }
        },

        _select2Wrapper: function (tag, multi, fetchFNC, nameKey) {
            nameKey = nameKey || 'name';

            var values = {
                width: '100%',
                placeholder: tag,
                allowClear: true,
                formatNoMatches: false,
                selection_data: false,
                fetch_rpc_fnc: fetchFNC,
                // --------Extend slide upload js (init tag function)-------
                initSelection: function (element, callback) {
                    if (multi) {
                        var data = [];
                        _.each(eval(element.val()), function (tag) {
                            data.push({ id: tag.id, text: tag.text });
                        });
                        callback(data);
                    }
                    else {
                        _.each(eval(element.val()), function (category) {
                            callback(category);
                        });
                    }
                },
                //-----------------------------------------------------
                formatSelection: function (data) {
                    if (data.tag) {
                        data.text = data.tag;
                    }
                    return data.text;
                },
                createSearchChoice: function (term, data) {
                    var addedTags = $(this.opts.element).select2('data');
                    if (_.filter(_.union(addedTags, data), function (tag) {
                        return tag.text.toLowerCase().localeCompare(term.toLowerCase()) === 0;
                    }).length === 0) {
                        if (this.opts.can_create) {
                            return {
                                id: _.uniqueId('tag_'),
                                create: true,
                                tag: term,
                                text: _.str.sprintf(_t("Create new %s '%s'"), tag, term),
                            };
                        } else {
                            return undefined;
                        }
                    }
                },
                fill_data: function (query, data) {
                    var self = this,
                        tags = {results: []};
                    _.each(data, function (obj) {
                        if (self.matcher(query.term, obj[nameKey])) {
                            tags.results.push({id: obj.id, text: obj[nameKey]});
                        }
                    });
                    query.callback(tags);
                },
                query: function (query) {
                    var self = this;
                    // fetch data only once and store it
                    if (!this.selection_data) {
                        this.fetch_rpc_fnc().then(function (data) {
                            self.can_create = data.can_create;
                            self.fill_data(query, data.read_results);
                            self.selection_data = data.read_results;
                        });
                    } else {
                        this.fill_data(query, this.selection_data);
                    }
                }
            };

            if (multi) {
                values['multiple'] = true;
            }

            return values;
        },

        _onEventAlldayChanged: function (ev) {
            if (this.$(ev.currentTarget).is(':checked')){
                this.$("#event_date #event_jq_date input.time").val('');
            }
            this.$("#event_date #event_jq_date input.time").closest('div').toggleClass('d-none', this.$(ev.currentTarget).is(':checked'));
        },

        _onTicketPricingMethodPChanged: function(ev) {
            if (this.$(ev.currentTarget).val() == 'times') {
                this.$(".price_timing").hide();
                this.$(".price_times").show();
                this.$("#price").removeAttr('disabled');
                this.$("#price").css('background-color', '#FFF');
                this.$('#min_request_unit').val('');
            } else {
                this.$(".price_timing").show();
                this.$(".price_times").hide();
                this.$("#price").attr({'disabled': 'disabled'});
                this.$("#price").css('background-color', '#DDD');
                this._onEventrequestNuitChange();
            }
        },

        // #endregion

        // #region : Organizer disabled/show, 之後如果有要遷移, 該區塊可保留於 dobtor_demand_marketplace 模組
        _onOrganizerChanged: function (ev) {
            this.$('#organizer_block').toggleClass('d-none');
        },
        // #endregion

        _onEventrequestNuitChange: function() {
            let min_unit = parseInt(this.$('#min_request_unit').val()) == 'NaN' ? 0 : parseInt(this.$('#min_request_unit').val());
            let unit = this.$('#select_unit').val() == 'per_hour' ? 60 : 1;
            this.$('#price').val(parseInt(min_unit * unit));
        },

        // #region : Address disabled/show
        _onOnlineAddressOptionChanged: function (ev) {
            this.$('#event_address').closest('div').toggleClass('d-none', !this.$(ev.currentTarget).is(':checked'));
            this.$("#event_address").attr('required', this.$(ev.currentTarget).is(':checked'));
            
            // #region: 如果地址選擇顯示，則必須選擇線上、線下其中一項
            if (this.$('.show_option_required').is(':checked'))
                this.$('.show_option_required').attr('required', false);
            else
                this.$('.show_option_required').attr('required', true);
            // #endregion
        },
        _onOfflineAddressOptionChanged: function (ev) {
            this.$('#offline_main').toggleClass('d-none', !this.$(ev.currentTarget).is(':checked'));

            if (this.$(ev.currentTarget).is(':checked'))
                this.$('.custom_offline_address_wrapper >div >div >input[type="text"]').attr('required', this.$(ev.currentTarget).is(':checked'));
            else
                this.$("#offline_main >div input").attr('required', false);
            
            // #region: 如果地址選擇顯示，則必須選擇線上、線下其中一項
            if (this.$('.show_option_required').is(':checked'))
                this.$('.show_option_required').attr('required', false);
            else
                this.$('.show_option_required').attr('required', true);
            // #endregion
        },
        _onAddressChanged: function (ev) {
            this.$('#address_block').toggleClass('d-none');

            if (this.$(ev.currentTarget).attr('id') == 'event_address_no_show') {
                this.$("#event_address").attr('required', false);
                this.$("#offline_main input").attr('required', false);
                this.$('.show_option_required').attr('required', false);
            } else {
                this.$('.show_option_required').attr('required', true);
                this.$('input[name="online_address_option"]').change();
                this.$('input[name="offline_address_option"]').change();
            }
        },
        // #endregion
    });

    publicWidget.registry.DemandPortalUpload = publicWidget.Widget.extend({
        selector: '.js_upload_demand_portal',
        xmlDependencies: ['/dobtor_demand_marketplace/static/src/xml/demand_portal_upload.xml'],
        events: {
            'click': '_onUploadClick',
        },
        _openDialog: function ($element) {
            var data = $element.data();
            return new DemandPortalUploadDialog(this, data).open();
        },

        _onUploadClick: function (ev) {
            ev.preventDefault();
            this._openDialog($(ev.currentTarget));
        },
    });

    publicWidget.registry.DemandTeamPortalUpload = publicWidget.Widget.extend({
        selector: '.js_upload_demand_team_portal',
        xmlDependencies: ['/dobtor_demand_marketplace/static/src/xml/demand_portal_upload.xml'],
        events: {
            'click': '_onUploadClick',
        },
        _openDialog: function ($element) {
            var data = $element.data();
            $.extend(data, {'is_team': true});
            return new DemandPortalUploadDialog(this, data).open();
        },

        _onUploadClick: function (ev) {
            ev.preventDefault();
            this._openDialog($(ev.currentTarget));
        },
    });


    return {
        DemandPortalUploadDialog: DemandPortalUploadDialog,
        DemandPortalUpload: publicWidget.registry.DemandPortalUpload,
        DemandTeamPortalUpload: publicWidget.registry.DemandTeamPortalUpload
    };
});
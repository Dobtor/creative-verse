odoo.define('dobtor_team.team_upload', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var publicWidget = require('web.public.widget');
    var wysiwygLoader = require('web_editor.loader');
    var utils = require('web.utils');
    var _t = core._t;

    var TeamUploadDialog = Dialog.extend({
        template: 'website.team.upload.modal',
        events: _.extend({}, Dialog.prototype.events, {
            'change input#upload': '_onChangeUpload',
        }),
        init: function (parent, options) {
            var buttons = [{
                    text: _t("Save"),
                    classes: 'ml-auto bg-o-color-1 save_disable',
                    click: this._onClickFormSubmit.bind(this)
                },
                {
                    text: _t("Discard"),
                    classes: 'save_disable',
                    close: true
                },
            ];
            this._super(parent, _.extend({}, {
                title: _t("Upload Team"),
                size: 'medium',
                dialogClass: 'team_upload_body',
                buttons: buttons,
            }, options || {}));
            this.file = {};
        },
        start: function () {
            this.$modal.find(".modal-header").addClass('team_upload_header');
            this.$footer.addClass('team_upload_footer');
            this.$footer.prepend('<div class="d-flex flex-column footer_error_msg w-100 mb-3"/>');

            // this._bindSelect2Dropdown();

            var toolbar = [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'clear']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['insert', ['link', 'picture']],
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
                    route: '/events/tag/search_read',
                    params: {
                        fields: ['name'],
                        domain: [],
                    }
                });
            }));
        },

        _onChangeUpload: function (ev) {
            var self = this;
            this._alertRemove();
    
            var $input = $(ev.currentTarget);
            var preventOnchange = $input.data('preventOnchange');
            var $custom_label = self.$('.custom-file-label');
    
            var file = ev.target.files[0];
            if (!file) {
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
            $('<div/>', {
                "class": 'alert alert-warning',
                id: 'upload-alert',
                role: 'alert'
            }).text(message).insertBefore(this.$('form'));
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
        
        _formValidateGetValues: function (forcePublished) {
            var values = _.extend({
                'name': this._formGetFieldValue('name'),
                'profile_content': this._formGetFieldValue('description') != '' ? this._formGetFieldValue('description') : ' ',
            }); 

            if (/^image\/.*/.test(this.file.type)) {
                _.extend(values, {
                    'image_1920': this.file.data,
                });
            }

            return values;
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
                    route: '/team/upload_team',
                    params: values,
                }).then(function (data) {
                    self._onFormSubmitDone(data);
                });
            }
        },

        _onFormSubmitDone: function (data) {
            if (data.error) {
                this._alertDisplay(data.error);
            } else {
                window.location = data.url;
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
                // -------init tag function--------------------------
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

        destroy: function () {
            if (this.__parentedParent){
                $(this.__parentedParent.$el).css('pointer-events', 'unset');
                $(this.__parentedParent.$el).css('opacity', 'unset');
            }
            this._super();
        },
    });

    publicWidget.registry.TeamUpload = publicWidget.Widget.extend({
        selector: '.js_upload_team',
        xmlDependencies: ['/dobtor_team/static/src/xml/team_upload.xml'],
        events: {
            'click': '_onUploadClick',
        },
        _openDialog: function ($element) {
            var data = $element.data();
            return new TeamUploadDialog(this, data).open();
        },

        _onUploadClick: function (ev) {
            ev.preventDefault();
            var target = $(ev.currentTarget);

            target.css('pointer-events', 'none');
            target.css('opacity', 0.65);
            this._openDialog($(ev.currentTarget));
        },
    });


    return {
        TeamUploadDialog: TeamUploadDialog,
        TeamUpload: publicWidget.registry.TeamUpload
    };
});
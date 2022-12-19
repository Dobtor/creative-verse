odoo.define('dobtor_user_profile.profile_share', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    
    publicWidget.registry.userProfileShare = publicWidget.Widget.extend({
        selector: '.db-profile__share_wrapper',
        events: {
            'click a.o_wprofile_js_social_share': '_onProfileSocialShare',
            'click .o_profile_copy_button': '_onReferralUrlCopy',
        },
        start: function() {
            this._get_facebook_share_href();
            this._get_line_share_href();

            return this._super.apply(this, arguments);
        },
        _get_facebook_share_href: function(){
            var parse_url = $('#parse_url').val();
            var link = "https://www.facebook.com/sharer/sharer.php?u=" +parse_url;
            $('#facebook_link').attr('href',link);
        },
        _get_line_share_href: function(){
            var parse_url = $('#parse_url').val();
            var link = "https://lineit.line.me/share/ui?url=" +parse_url;
            $('#line_link').attr('href',link);
        },
        _onProfileSocialShare: function (ev) {
            ev.preventDefault();
            var popUpURL = $(ev.currentTarget).attr('href');
            var popUp = window.open(popUpURL, 'Share Dialog', 'width=626,height=436');
            $(window).on('focus', function () {
                if (popUp.closed) {
                    $(window).off('focus');
                }
            });
        },

        _onReferralUrlCopy: function (ev) {
            ev.preventDefault();
            var $clipboardBtn = $(ev.currentTarget);
            $clipboardBtn.tooltip({title: "Copied !", trigger: "manual", placement: "bottom"});
            var self = this;
            var clipboard = new ClipboardJS('.o_profile_copy_button', {
                text: function () {
                    return self.$('.o_wprofile_js_referral_url').val();
                },
                container: this.el
            });
            clipboard.on('success', function () {
                clipboard.destroy();
                $clipboardBtn.tooltip('show');
                _.delay(function () {
                    $clipboardBtn.tooltip("hide");
                }, 800);
            });
            clipboard.on('error', function (e) {
                clipboard.destroy();
            })
        },
    });
});
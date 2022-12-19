odoo.define('dobtor_user_profile.member_chapternav_scroll', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');

    var _t = core._t;


    publicWidget.registry.member_chapternav_scroll = publicWidget.Widget.extend({
        selector: '.memberchapternav',
        events: {
            'click .member_chapternav_paddle_left': '_onClickLeft',
            'click .member_chapternav_paddle_right': '_onClickRight',
        },

        start: function () {
            var def = this._super.apply(this, arguments);
            var self = this;
            // duration of scroll animation
            this.scrollDuration = 300;
            // get some relevant size for the paddle triggering point
            this.paddleMargin = 10;
            this.menuInvisibleSize = this._updateInvisibleSize(this.$el);
            this._paddleDisplay(this.$el);
            
            $(window).on('resize', function() {
                self.menuInvisibleSize = self._updateInvisibleSize(self.$el);
                self._paddleDisplay(self.$el);
            });

            // finally, what happens when we are actually scrolling the menu
            this.$('.member_chapternav_items').on('scroll', function(ev) {
                self._paddleDisplay(self.$el);
            });

            return Promise.all([def]);
        },

        _onClickLeft: function (ev) {
            var $target = $(ev.currentTarget);
            $target.parents(".memberchapternav").first().find('.member_chapternav_items').first().animate( { scrollLeft: '0' }, this.scrollDuration);
        },

        _onClickRight: function (ev) {
            var $target = $(ev.currentTarget);
            $target.parents(".memberchapternav").first().find('.member_chapternav_items').first().animate( { scrollLeft: this.menuInvisibleSize.toFixed(0) }, this.scrollDuration);
        },

        _getMenuPosition: function (target) {
            return target.scrollLeft();
        },

        _paddleDisplay: function ($el){
            // get how much have we scrolled so far
            var menuPosition = this._getMenuPosition($el.find('.member_chapternav_items'));
            var menuEndOffset = this.menuInvisibleSize - this.paddleMargin;

            var leftPaddle = $el.find('.member_chapternav_paddle_left');
            var rightPaddle = $el.find('.member_chapternav_paddle_right');
            // show & hide the paddles 
            // depending on scroll position
            if (this.menuInvisibleSize == 0){
                $(leftPaddle).addClass('d-none');
                $(rightPaddle).addClass('d-none');
            } else if (menuPosition <= this.paddleMargin) {
                $(leftPaddle).addClass('d-none');
                $(rightPaddle).removeClass('d-none');
            } else if (menuPosition < menuEndOffset) {
                // show both paddles in the middle
                $(leftPaddle).removeClass('d-none');
                $(rightPaddle).removeClass('d-none');
            } else if (menuPosition >= menuEndOffset) {
                $(leftPaddle).removeClass('d-none');
                $(rightPaddle).addClass('d-none');
            }
        },

        _updateInvisibleSize: function ($el) {
            var mainWrapperSize = $el.outerWidth();
            var targerSize = $el.find('.member_chapternav_items').first()[0].scrollWidth;

            return targerSize - mainWrapperSize;
        },
    });
});
    
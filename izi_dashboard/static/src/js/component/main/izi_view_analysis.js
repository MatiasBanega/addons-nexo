odoo.define('izi_dashboard.IZIViewAnalysis', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    
    var IZIViewVisual = require('izi_dashboard.IZIViewVisual');
    var IZISelectFilterTemp = require('izi_dashboard.IZISelectFilterTemp');
    var IZIViewAnalysis = Widget.extend({
        template: 'IZIViewAnalysis',

        /**
         * @override
         */
        init: function (parent) {
            var self = this;
            this._super.apply(this, arguments);
            
            self.parent = parent;
            self.$visual;
            self.$title;
            self.$filter;
            self.analysis_id;
        },

        willStart: function () {
            var self = this;

            return this._super.apply(this, arguments).then(function () {
                return self.load();
            });
        },

        load: function () {
            var self = this;
        },

        start: function() {
            var self = this;
            this._super.apply(this, arguments);

            am4core.useTheme(am4themes_animated);

            self.$title = self.$el.find('.izi_dashboard_block_header .izi_dashboard_block_title');
            
            // Add Component Visual View
            self.$visual = new IZIViewVisual(self);
            self.$visual.appendTo(self.$el.find('.izi_dashboard_block_content'));

            // Add Component Filters
            self.$filter = new IZISelectFilterTemp(self, self.$visual);
            self.$filter.appendTo(self.$el.find('.izi_dashboard_block_header'));
        },

        _setAnalysisId: function (analysis_id) {
            var self = this;
            self.analysis_id = analysis_id;
            if (self.$filter) {
                self.$filter.analysis_id = analysis_id;
                self.$filter._loadFilters();
            }
        },
    });

    return IZIViewAnalysis;
});
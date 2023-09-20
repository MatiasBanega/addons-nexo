odoo.define('izi_dashboard.IZIViewVisual', function (require) {
    "use strict";

    var Widget = require('web.Widget');

    var IZIViewVisual = Widget.extend({
        template: 'IZIViewVisual',
        events: {
            'click input': '_onClickInput',
            'click button': '_onClickButton',
        },

        /**
         * @override
         */
        init: function (parent, args) {
            this._super.apply(this, arguments);
            this.interval;
            this.parent = parent;
            this.grid;
            this.index = 0;
            if (args) {
                this.block_id = args.block_id;
                this.analysis_id = args.analysis_id;
                this.filters = args.filters;
                this.refresh_interval = args.refresh_interval;
                this.index = args.index;
            }
            am4core.options.autoDispose = false;
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

        start: function () {
            var self = this;
            this._super.apply(this, arguments);
            var args = {}
            if (self.filters) {
                args.filters = self.filters;
            }
            self._renderVisual(args);
            if (self.refresh_interval && self.refresh_interval >= 10) {
                var readyInterval = true;
                am4core.options.autoDispose = true;
                self.interval = setInterval(function () {
                    if (readyInterval) {
                        readyInterval = false;
                        self._renderVisual(args, function() {
                            readyInterval = true;
                        });
                    }
                }, self.refresh_interval * 1000);
            }
        },

        /**
         * Called By Others
         */
        _setAnalysisId: function (analysis_id) {
            var self = this;
            self.analysis_id = analysis_id;
        },

        _renderVisual: function (args) {
            var self = this;
            self._deleteVisual();
            if (self.analysis_id) {
                self._getDataAnalysis(args, function (result) {
                    setTimeout(function() {
                        self.parent.$title.html(result.analysis_name);
                        self._makeChart(result);
                    }, Math.floor(self.index/3)*1500);
                })
            }
        },

        tableToLocaleString: function(table_data) {
            var new_table_data = []
            table_data.forEach(t_data => {
                var new_t_data = []
                t_data.forEach(dt => {
                    if (typeof dt == 'number')
                        dt = dt.toLocaleString()
                    new_t_data.push(dt);
                });
                new_table_data.push(new_t_data);
            });
            return new_table_data;
        },

        _makeChart: function (result) {
            var self = this;

            // TODO: Make it more elegant
            self.$el.parent().removeClass('izi_view_background');
            self.$el.removeClass('izi_view_scrcard_container scorecard scorecard-sm');
            self.$el.parents(".izi_dashboard_block_item").removeClass("izi_dashboard_block_item_v_background");

            var visual_type = result.visual_type;
            var data = result.data;
            var table_data = result.values;
            var columns = result.fields;

            var idElm = `visual_${self.analysis_id}`;
            if (self.block_id) {
                idElm = `block_${self.block_id}_${idElm}`;
            }
            self.$el.attr('id', idElm);
            if ($(`#${idElm}`).length == 0) return false;
            var visual = new amChartsComponent({
                title: result.analysis_name,
                idElm: idElm,
                data: data,
                dimension: result.dimensions[0], // TODO: Only one dimension?
                metric: result.metrics, // TODO: metric or metrics?
                // title: "Nama Analysis",

                legendPosition: result.visual_config_values.legendPosition,
                legendHeatmap: result.visual_config_values.legendHeatmap,
                area: result.visual_config_values.area,
                stacked: result.visual_config_values.stacked,
                innerRadius: result.visual_config_values.innerRadius,
                circleType: result.visual_config_values.circleType,
                labelSeries: result.visual_config_values.labelSeries,
                currency_code: result.visual_config_values.currency_code,
                particle: result.visual_config_values.particle,
                trends: result.visual_config_values.trends,
                trendLine: result.visual_config_values.trendLine,
                mapView: result.visual_config_values.mapView
            });

            if (visual_type == 'table') {
                if (!self.grid) {
                    self.grid = new gridjs.Grid({
                        columns: columns,
                        data: self.tableToLocaleString(table_data),
                        sort: true,
                        pagination: true,
                        resizable: true,
                        // search: true,
                    }).render($(`#${idElm}`).get(0));
                } else {
                    self.grid.updateConfig({
                        columns: columns,
                        data: table_data,
                    }).forceRender();
                }
            }
            else if (visual_type == 'pie') {
                visual.makePieChart();
            }
            else if (visual_type == 'radar') {
                visual.makeRadarChart();
            }
            else if (visual_type == 'flower') {
                visual.makeFlowerChart();
            }
            else if (visual_type == 'radialBar') {
                visual.makeRadialBarChart();
            }
            else if (visual_type == 'bar') {
                visual.makeBarChart();
            }
            else if (visual_type == 'row') {
                visual.makeRowChart();
            }
            else if (visual_type == 'bullet_bar') {
                visual.makeBulletBarChart();
            }
            else if (visual_type == 'bullet_row') {
                visual.makeBulletRow();
            }
            else if (visual_type == 'row_line') {
                visual.makeRowLine();
            }
            else if (visual_type == 'bar_line') {
                visual.makeBarLineChart();
            }
            else if (visual_type == 'line') {
                visual.makeLineChart();
            }
            else if (visual_type == 'scatter') {
                visual.makeScatterChart();
            }
            else if (visual_type == 'heatmap_geo') {
                visual.makeHeatmapGeo();
            }
            else if (visual_type == 'scrcard_basic') {

                if ((self.el.id).indexOf('block') === -1) { // layout ketika di preview chart
                    self.$el.parents(".izi_dashboard_block_item").addClass("izi_dashboard_block_item_v_background");
                    self.$el.parent().addClass('izi_view_background');
                    self.$el.addClass('izi_view_scrcard_container');
                }else{ // layout ketika di block Dashboard 
                    self.$el.parents(".izi_dashboard_block_item").find(".izi_dashboard_block_title").text("");
                    self.$el.parents(".izi_dashboard_block_item").find(".izi_dashboard_block_header").addClass("izi_dashboard_block_btn_config");                    
                }
                visual.makeScorecardBasic();
            }
            else if (visual_type == 'scrcard_trend') {

                if ((self.el.id).indexOf('block') === -1) { // layout ketika di preview chart
                    self.$el.parents(".izi_dashboard_block_item").addClass("izi_dashboard_block_item_v_background");
                    self.$el.parent().addClass('izi_view_background');
                    self.$el.addClass('izi_view_scrcard_container');
                }else{ // layout ketika di block Dashboard 
                    self.$el.parents(".izi_dashboard_block_item").find(".izi_dashboard_block_title").text("");
                    self.$el.parents(".izi_dashboard_block_item").find(".izi_dashboard_block_header").addClass("izi_dashboard_block_btn_config");                    
                }
                visual.makeScorecardTrend();
            }
            else if (visual_type == 'scrcard_progress') {

                if ((self.el.id).indexOf('block') === -1) { // layout ketika di preview chart
                    self.$el.parents(".izi_dashboard_block_item").addClass("izi_dashboard_block_item_v_background");
                    self.$el.parent().addClass('izi_view_background');
                    self.$el.addClass('izi_view_scrcard_container');
                }else{ // layout ketika di block Dashboard 
                    self.$el.parents(".izi_dashboard_block_item").find(".izi_dashboard_block_title").text("");
                    self.$el.parents(".izi_dashboard_block_item").find(".izi_dashboard_block_header").addClass("izi_dashboard_block_btn_config");                    
                }
                visual.makeScorecardProgress();
            }
        },
        _deleteVisual: function () {
            var self = this;
            self.$el.empty();
        },

        _getDataAnalysis: function (args, callback) {
            var self = this;
            if (self.analysis_id) {
                self._rpc({
                    model: 'izi.analysis',
                    method: 'get_analysis_data_dashboard',
                    args: [self.analysis_id],
                    kwargs: args,
                }).then(function (result) {
                    // console.log('Success Get Data Analysis', result);
                    callback(result);
                })
            }
        },

        _onClickInput: function (ev) {
            var self = this;
        },

        _onClickButton: function (ev) {
            var self = this;
        }
    });

    return IZIViewVisual;
});
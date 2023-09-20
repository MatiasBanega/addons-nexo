odoo.define('izi_dashboard.IZIConfigAnalysis', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var core = require('web.core');
    var view_dialogs = require('web.view_dialogs');
    var _t = core._t;
    var QWeb = core.qweb;

    var IZIAutocomplete = require('izi_dashboard.IZIAutocomplete');
    var IZISelectAnalysis = require('izi_dashboard.IZISelectAnalysis');
    var IZISelectDimension = require('izi_dashboard.IZISelectDimension');
    var IZISelectSort = require('izi_dashboard.IZISelectSort');
    var IZISelectFilter = require('izi_dashboard.IZISelectFilter');
    var IZISelectMetric = require('izi_dashboard.IZISelectMetric');
    var IZIConfigAnalysis = Widget.extend({
        template: 'IZIConfigAnalysis',
        events: {
            'click input': '_onClickInput',
            'click button': '_onClickButton',
            'click .izi_select_analysis': '_onClickSelectAnalysis',
            'click .izi_select_visual': '_onChangeVisualType',

            'click .izi_add_metric': '_onClickAddMetric',
            'click .izi_add_dimension': '_onClickAddDimension',
            'click .izi_add_sort': '_onClickAddSort',
            'click .izi_add_filter': '_onClickAddFilter',
            'click .izi_remove_metric_item': '_onClickRemoveMetric',
            'click .izi_remove_dimension_item': '_onClickRemoveDimension',
            'click .izi_remove_sort_item': '_onClickRemoveSort',
            'click .izi_remove_filter_item': '_onClickRemoveFilter',
            'click .izi_select_calculation': '_onClickSelectCalculation',
            'click .izi_select_format': '_onClickSelectFormat',
            'click .izi_select_sort_direction': '_onClickSelectSortDirection',

            'click .izi_add_dashboard_block': '_onClickAddDashboardBlock',

            'click .izi_tab_data': '_onClickTabData',
            'click .izi_tab_visual': '_onClickTabVisual',

            'change .izi_visual_config': '_onChangeVisualConfig',
            'change .izi_change_limit': '_onChangeLimit',

            'click .izi_update_current_filter_item': '_onUpdateCurrentFilter',
        },

        /**
         * @override
         */
        init: function (parent, $viewAnalysis) {
            var self = this;
            self._super.apply(self, arguments);
            self.parent = parent;
            if (parent.props) self.props = parent.props;
            self.$viewAnalysis = $viewAnalysis;

            // Element
            self.$selectTable;
            self.$selectAnalysis;
            self.$selectMetric;
            self.$selectDimension;
            self.$selectSort;
            self.$selectFilter;
            self.$selectUser;
            self.$tabData;
            self.$tabVisual;
            self.$tabContentData;
            self.$tabContentVisual;
            self.$selectDashboard;

            // Values
            self.selectedTableFields = [];
            self.selectedTable;
            self.selectedAnalysis;
            self.selectedAnalysisName;
            self.selectedVisualType;
            self.selectedAnalysisData = false;
            self.selectedDashboard;
            self.selectedDashboardName;
            self.changeLimit;
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

            // Element
            self.$selectTable = self.$('.izi_select_table');
            self.$selectAnalysis = self.$('.izi_select_analysis');
            self.$changeLimit = self.$('.izi_change_limit');

            // Current
            self.$currentMetric = self.$('.izi_current_metric');
            self.$currentDimension = self.$('.izi_current_dimension');
            self.$currentSort = self.$('.izi_current_sort');
            self.$currentFilter = self.$('.izi_current_filter');

            // Tab
            self.$tabData = self.$('.izi_tab_data');
            self.$tabVisual = self.$('.izi_tab_visual');
            self.$tabContentData = self.$('.izi_tab_content_data');
            self.$tabContentVisual = self.$('.izi_tab_content_visual');

            self.$selectVisualContainer = self.$('.izi_select_visual_container');
            self.$changeLimitContainer = self.$('.izi_change_limit_container');
            self._renderVisualTypes();

            self.$selectVisualConfigContainer = self.$('.izi_select_visual_config_container');
            self.$addDasboardContainer = self.$('.izi_add_dashboard_container');
            self.$buttonAddDashboardBlock = self.$('.izi_add_dashboard_block');

            // Dashboard
            self._loadDashboards();

            // Check Context From Actions
            self._checkActionContext();
        },

        /**
         * Load Method
         */


        /**
         * Handler Method
         */
        _onClickInput: function (ev) {
            var self = this;
        },

        _onClickButton: function (ev) {
            var self = this;
        },

        _onClickSelectAnalysis: function (ev) {
            var self = this;
            // Add Dialog
            var $select = new IZISelectAnalysis(self)
            $select.appendTo($('body'));
        },

        _selectAnalysis: function (id, name, table, visual_type) {
            var self = this;
            self.selectedAnalysis = id;
            self.selectedAnalysisName = name;
            self.selectedVisualType = visual_type;
            self.$viewAnalysis._setAnalysisId(id);
            self.$selectAnalysis.find('.izi_title').text(name);
            self.$selectAnalysis.find('.izi_subtitle').text(table);
            self._loadAnalysisInfo();
            self._renderVisual();
            self._renderVisualConfigs();
            self.$buttonAddDashboardBlock.show();
            self.$addDasboardContainer.show();
            self.$changeLimitContainer.show();

            self._onClickAddMetric();
            self._onClickAddDimension();
            self._onClickAddFilter();
            self._onClickAddSort();
        },

        _loadAnalysisInfo: function () {
            var self = this;
            if (self.selectedAnalysis) {
                self._rpc({
                    model: 'izi.analysis',
                    method: 'ui_get_analysis_info',
                    args: [self.selectedAnalysis],
                }).then(function (result) {
                    // console.log('Get Analysis Info', result)
                    self._setActiveClass(result.visual_type);
                    // if dashbord has been selected then hide select2 dropdown dashboard
                    if (self.selectedDashboard) {
                        
                        self.$('#s2id_izi_select2_dashboard').hide()
                    }
                    // Metric
                    self.metrics = result.metrics;
                    self.$currentMetric.empty();
                    self.metrics.forEach(metric => {
                        var $content = $(QWeb.render('IZICurrentMetricItem', {
                            name: metric.name,
                            id: metric.id,
                            field_type: metric.field_type,
                            calculation: metric.calculation,
                            metric_id: metric.metric_id,
                            sort: metric.sort,
                        }));
                        self.$currentMetric.append($content)
                    });
                    // Dimensions
                    self.dimensions = result.dimensions;
                    self.$currentDimension.empty();
                    self.dimensions.forEach(dimension => {
                        var $content = $(QWeb.render('IZICurrentDimensionItem', {
                            name: dimension.name,
                            id: dimension.id,
                            field_type: dimension.field_type,
                            dimension_id: dimension.dimension_id,
                            field_icon: IZIFieldIcon.getIcon(dimension.field_type),
                            field_format: dimension.field_format || 'FORMAT',
                            sort: dimension.sort,
                        }));
                        self.$currentDimension.append($content)
                    });
                    // Sorts
                    self.sorts = result.sorts;
                    self.$currentSort.empty();
                    self.sorts.forEach(sort => {
                        var $content = $(QWeb.render('IZICurrentSortItem', {
                            name: sort.name,
                            id: sort.id,
                            field_type: sort.field_type,
                            sort_id: sort.sort_id,
                            field_icon: IZIFieldIcon.getIcon(sort.field_type),
                            field_format: sort.field_format || 'FORMAT',
                            field_calculation: sort.field_calculation,
                            sort: sort.sort,
                        }));
                        self.$currentSort.append($content)
                    });
                    // Filters
                    self.filters = result.filters;
                    self.$currentFilter.empty();
                    self.filters.forEach(filter => {
                        var $content = $(QWeb.render('IZICurrentFilterItem', {
                            name: filter.name,
                            id: filter.id,
                            field_type: filter.field_type,
                            filter_id: filter.filter_id,
                            field_icon: IZIFieldIcon.getIcon(filter.field_type),
                            filter_operators: result.filter_operators,
                            current_operator_id: filter.operator_id,
                            condition: filter.condition,
                            value: filter.value,
                        }));
                        self.$currentFilter.append($content)
                    });
                    // Limit
                    self.$changeLimit.val(result.limit);
                })
            }
        },

        _renderVisualTypes: function () {
            var self = this;
            self._rpc({
                model: 'izi.visual.type',
                method: 'search_read',
                args: [[], ['id', 'name', 'icon', 'title']],
            }).then(function (results) {
                // console.log('Get Visual Types', results)
                self.$selectVisualContainer.empty();
                results.forEach(vt => {
                    self.$selectVisualContainer.append(
                        `<div class="izi_btn izi_select_visual flex-column" data-visual-type="${vt.name}" data-visual-type-id="${vt.id}">
                            <span class="material-icons">${vt.icon}</span> ${vt.title}
                        </div>`
                    )
                });
            })
        },

        _renderVisualConfigs: function () {
            var self = this;
            self._rpc({
                model: 'izi.visual.type',
                method: 'get_visual_config',
                args: [[], self.selectedVisualType, self.selectedAnalysis],
            }).then(function (results) {
                // console.log('Get Visual Config', results)
                self.$selectVisualConfigContainer.empty();
                results.forEach(vc => {
                    if (vc.config_type == 'input_string' || vc.config_type == 'input_number') {
                        let input_type = 'text';
                        if (vc.config_type == 'input_number') {
                            input_type = 'number';
                        }
                        self.$selectVisualConfigContainer.append(`
                            <div class="flex-body mb-3">
                                <label for="${vc.name}${vc.id}" class="flex-1 col-form-label izi_subtitle">${vc.title}</label>
                                <div class="input-group flex-1">
                                    <input type="${input_type}" class="form-control izi_visual_config" id="${vc.name}${vc.id}" placeholder="" data-visual-config="${vc.name}" data-visual-config-id="${vc.id}" data-visual-config-type="${vc.config_type}" data-analysis-visual-config-id="${vc.analysis_visual_config_id}"></input>
                                </div>
                            </div>
                        `);
                        let input_value = vc.config_value != null ? vc.config_value : vc.default_config_value;
                        $(`#${vc.name}${vc.id}`).val(input_value);

                    } else if (vc.config_type == 'toggle') {
                        self.$selectVisualConfigContainer.append(`
                        <div class="flex-body mb-3">
                            <label for="" class="flex-1 col-form-label izi_subtitle">${vc.title}</label>
                            <div class="flex-1">
                                <label class="toggle-switchy" for="${vc.name}${vc.id}" data-size="xs" data-style="rounded" data-text="false">
                                    <input checked="" class="izi_visual_config" type="checkbox" id="${vc.name}${vc.id}" data-visual-config="${vc.name}" data-visual-config-id="${vc.id}" data-visual-config-type="${vc.config_type}" data-analysis-visual-config-id="${vc.analysis_visual_config_id}"></input>
                                    <span class="toggle">
                                        <span class="switch"></span>
                                    </span>
                                </label>
                            </div>
                        </div>
                        `);
                        let toggle_value = vc.config_value != null ? vc.config_value : vc.default_config_value;
                        $(`#${vc.name}${vc.id}`).prop("checked", toggle_value);

                    } else if (vc.config_type == 'selection_string' || vc.config_type == 'selection_number') {
                        self.$selectVisualConfigContainer.append(`
                        <div class="flex-body mb-3">
                            <label for="${vc.name}${vc.id}" class="flex-1 col-form-label izi_subtitle">${vc.title}</label>
                            <div class="input-group flex-1">
                                <select id="${vc.name}${vc.id}" class="form-control izi_visual_config" data-visual-config="${vc.name}" data-visual-config-id="${vc.id}" data-visual-config-type="${vc.config_type}" data-analysis-visual-config-id="${vc.analysis_visual_config_id}">
                                </select>
                            </div>
                        </div>
                        `);
                        (vc.visual_config_values).forEach(vcv => {
                            $(`#${vc.name}${vc.id}`).append(`
                                <option class="izi_visual_config_value" value="${vcv.name}" data-visual-config-value-id="${vcv.id}">${vcv.title}</option>
                            `);
                        });
                        let selection_value = vc.config_value != null ? vc.config_value : vc.default_config_value;

                        if (vc.name === "mapView") {
                            var countriesId = Object.keys(am4geodata_data_countries2);
                            selection_value = selection_value.toUpperCase();
                            countriesId.forEach((values, i) => {
                                if (am4geodata_data_countries2[countriesId[i]].maps[0] != undefined) {
                                    $(`#${vc.name}${vc.id}`).append(`
                                        <option class="izi_visual_config_value" value=`+ countriesId[i] +`>` + am4geodata_data_countries2[countriesId[i]].country + `</option>
                                    `);
                                };
                            });
                        };

                        $(`#${vc.name}${vc.id}`).val(selection_value);
                    }
                });
            })
        },

        _onClickAddMetric: function (ev) {
            var self = this;

            // Add Metric Component
            if (self.selectedAnalysis) {
                if (self.$selectMetric)
                    self.$selectMetric.destroy();
                self.$selectMetric = new IZISelectMetric(self)
                self.$selectMetric.appendTo(self.$el.find('.izi_select_metric_container'));
            }
        },

        _onClickAddDimension: function (ev) {
            var self = this;

            // Add Dimension Component
            if (self.selectedAnalysis) {
                if (self.$selectDimension)
                    self.$selectDimension.destroy();
                self.$selectDimension = new IZISelectDimension(self)
                self.$selectDimension.appendTo(self.$el.find('.izi_select_dimension_container'));
            }
        },

        _onClickAddSort: function (ev) {
            var self = this;

            // Add Sort Component
            if (self.selectedAnalysis) {
                if (self.$selectSort)
                    self.$selectSort.destroy();
                self.$selectSort = new IZISelectSort(self)
                self.$selectSort.appendTo(self.$el.find('.izi_select_sort_container'));
            }
        },

        _onClickAddFilter: function (ev) {
            var self = this;

            // Add Filter Component
            if (self.selectedAnalysis) {
                if (self.$selectFilter)
                    self.$selectFilter.destroy();
                self.$selectFilter = new IZISelectFilter(self)
                self.$selectFilter.appendTo(self.$el.find('.izi_select_filter_container'));
            }
        },

        _onClickRemoveMetric: function (ev) {
            var self = this;
            var metric_id = $(ev.target).data('metric');
            // console.log('Remove Metric', metric_id);
            if (self.selectedAnalysis) {
                self._rpc({
                    model: 'izi.analysis',
                    method: 'ui_remove_metric',
                    args: [self.selectedAnalysis, metric_id],
                }).then(function (result) {
                    self._loadAnalysisInfo();
                    self._onClickAddMetric();
                    self._renderVisual();
                })
            }
        },

        _onClickRemoveDimension: function (ev) {
            var self = this;
            var dimension_id = $(ev.target).data('dimension');
            // console.log('Remove Dimension', dimension_id);
            if (self.selectedAnalysis) {
                self._rpc({
                    model: 'izi.analysis',
                    method: 'ui_remove_dimension',
                    args: [self.selectedAnalysis, dimension_id],
                }).then(function (result) {
                    self._loadAnalysisInfo();
                    self._onClickAddDimension();
                    self._renderVisual();
                })
            }
        },

        _onClickRemoveSort: function (ev) {
            var self = this;
            var sort_id = $(ev.target).data('sort_id');
            if (self.selectedAnalysis) {
                self._rpc({
                    model: 'izi.analysis',
                    method: 'ui_remove_sort',
                    args: [self.selectedAnalysis, sort_id],
                }).then(function (result) {
                    self._loadAnalysisInfo();
                    self._onClickAddSort();
                    self._renderVisual();
                })
            }
        },

        _onClickRemoveFilter: function (ev) {
            var self = this;
            var filter_id = $(ev.target).data('filter_id');
            if (self.selectedAnalysis) {
                self._rpc({
                    model: 'izi.analysis',
                    method: 'ui_remove_filter',
                    args: [self.selectedAnalysis, filter_id],
                }).then(function (result) {
                    self._loadAnalysisInfo();
                    self._onClickAddFilter();
                    self._renderVisual();
                })
            }
        },

        _onUpdateCurrentFilter: function (ev) {
            var self = this;
            var filter_id = $(ev.currentTarget).data('filter_id');
            var field_id = $(ev.currentTarget).data('id');
            var logical_operator = $('#current_form_filter_' + field_id).find('#current_condition_' + field_id).val();
            var operator_id = $('#current_form_filter_' + field_id).find('#current_operator_' + field_id).val();
            var value = $('#current_form_filter_' + field_id).find('#current_value_' + field_id).val();
            if (self.selectedAnalysis) {
                var data = {
                    'filter_id': filter_id,
                    'field_id': field_id,
                    'operator_id': operator_id,
                    'condition': logical_operator,
                    'value': value,
                }
                self._rpc({
                    model: 'izi.analysis',
                    method: 'ui_update_filter_by_field',
                    args: [self.selectedAnalysis, data],
                }).then(function (result) {
                    self._loadAnalysisInfo();
                    self._onClickAddFilter();
                    self._renderVisual();
                })
            }
        },

        _onClickSelectCalculation: function (ev) {
            var self = this;
            var calculation = $(ev.currentTarget).data('calculation');
            var metric_id = $(ev.currentTarget).data('metric');
            if (calculation && metric_id) {
                var data = {
                    'calculation': calculation,
                }
                self._rpc({
                    model: 'izi.analysis.metric',
                    method: 'write',
                    args: [[parseInt(metric_id)], data],
                }).then(function (result) {
                    self._loadAnalysisInfo();
                    self._renderVisual();
                })
            }
        },

        _onClickSelectFormat: function (ev) {
            var self = this;
            var format = $(ev.currentTarget).data('format');
            var dimension_id = $(ev.currentTarget).data('dimension');
            if (format && dimension_id) {
                var data = {
                    'field_format': format,
                }
                self._rpc({
                    model: 'izi.analysis.dimension',
                    method: 'write',
                    args: [[parseInt(dimension_id)], data],
                }).then(function (result) {
                    self._loadAnalysisInfo();
                    self._onClickAddDimension();
                    self._renderVisual();
                })
            }
        },

        _onClickSelectSortDirection: function (ev) {
            var self = this;
            var sort = $(ev.currentTarget).data('sort');
            var sort_id = $(ev.currentTarget).data('sort_id');
            if (sort && sort_id) {
                var data = {
                    'sort': sort != 'none' ? sort : false,
                }
                self._rpc({
                    model: 'izi.analysis.sort',
                    method: 'write',
                    args: [[parseInt(sort_id)], data],
                }).then(function (result) {
                    self._loadAnalysisInfo();
                    self._onClickAddDimension();
                    self._renderVisual();
                });
            }
        },

        _setActiveClass: function (visual_type) {
            $('.izi_select_visual').removeClass('active');
            if (visual_type) {
                $(`.izi_select_visual[data-visual-type="${visual_type}"]`).addClass('active');
            }
        },

        _renderVisual: function (args) {
            var self = this;
            if (self.$viewAnalysis.$visual && self.selectedAnalysis) {
                self.$viewAnalysis.$visual._setAnalysisId(self.selectedAnalysis);
                self.$viewAnalysis.$visual._renderVisual(args);

                
                if (self.selectedVisualType == 'heatmap_geo') {
                    Swal.fire({
                        title: 'Map Viz',
                        icon: 'info',
                        html:
                        '<div style=`text-align : left`>Needs to have 2 Dimensions :'+
                        '<br></br>'+
                        '<li>First dimension as the Country code.</li>' +
                        '<li>Second dimension as the State code.</li>'+
                        '<small>e.g. " ID-RI " for Riau province of Indonesia </small><br></br>' +
                        '<small>Reference by <a href="https://www.iso.org/obp/ui/#search/code/">ISO 3166-2 code</a> </small></div>',
                      });
                }else if (self.selectedVisualType == 'scatter') {
                    Swal.fire({
                        title: 'Scatter Plot',
                        icon: 'info',
                        html:
                        'Needs to have 2 Metrics :'+
                        '<br></br>'+
                        '<li>1st Metric as the X axis</li>' +
                        '<li>2nd Metric as the Y axis</li>'+
                        '<li>3rd Metric as the value(optional)</li>',
                   });
                };
            }
        },

        _onChangeVisualType: function (ev) {
            var self = this;
            if (self.selectedAnalysis) {
                self.selectedVisualType = $(ev.currentTarget).data('visual-type');
                self._rpc({
                    model: 'izi.analysis',
                    method: 'save_analysis_visual_type',
                    args: [[self.selectedAnalysis], self.selectedVisualType],
                }).then(function (result) {
                    self._setActiveClass(self.selectedVisualType);
                    self._renderVisual();
                    self._renderVisualConfigs();
                });
            }
        },

        _onClickSaveAnalysisVisual: function () {
            var self = this;
            if (self.selectedAnalysis) {
                let config_values = []
                $('.izi_select_visual_config_container .izi_visual_config').each(function () {
                    let config_type = $(this).attr('data-visual-config-type');
                    let config_value = null;
                    let visual_config_value_id = null;
                    let analysis_visual_config_id = $(this).attr('data-analysis-visual-config-id');
                    if (config_type == "input_string" || config_type == "input_number") {
                        config_value = $(this).val();
                    } else if (config_type == "toggle") {
                        config_value = $(this).is(":checked");
                    } else if (config_type == "selection_string" || config_type == "selection_number") {
                        config_value = $(this).val();
                        visual_config_value_id = $(`#${$(this).attr("id")} option:selected`).attr('data-visual-config-value-id');
                    }
                    config_values.push({
                        'id': analysis_visual_config_id != 'null' ? parseInt(analysis_visual_config_id) : null,
                        'analysis_id': self.selectedAnalysis,
                        'visual_config_id': parseInt($(this).attr('data-visual-config-id')),
                        'visual_config_value_id': visual_config_value_id != null ? parseInt(visual_config_value_id) : null,
                        'string_value': String(config_value),
                    })
                })

                self._rpc({
                    model: 'izi.analysis',
                    method: 'save_analysis_visual_config',
                    args: [[self.selectedAnalysis], self.selectedVisualType, config_values],
                }).then(function (result) {
                    self._renderVisual();
                    self._renderVisualConfigs();
                    new swal('Success', 'Analysis Visual has been saved successfully', 'success');
                })
            }
        },

        _onClickAddDashboardBlock: function () {
            var self = this;
            if (self.selectedAnalysis && self.selectedDashboard) {
                self._rpc({
                    model: 'izi.dashboard.block',
                    method: 'create',
                    args: [{
                        'analysis_id': self.selectedAnalysis,
                        'dashboard_id': self.selectedDashboard,
                    }],
                }).then(function (result) {
                    new swal('Success', `${self.selectedAnalysisName} has been added to ${self.selectedDashboardName}`, 'success');
                })
            }
        },

        _onClickTabData: function () {
            var self = this;
            self.$tabData.addClass('active');
            self.$tabVisual.removeClass('active');
            self.$tabContentData.show();
            self.$tabContentVisual.hide();
        },

        _onClickTabVisual: function () {
            var self = this;
            self.$tabData.removeClass('active');
            self.$tabVisual.addClass('active');
            self.$tabContentData.hide();
            self.$tabContentVisual.show();
        },

        _onChangeVisualConfig: function (ev) {
            var self = this;
            if (self.selectedAnalysis) {
                let config_values = []
                $('.izi_select_visual_config_container .izi_visual_config').each(function () {
                    let config_type = $(this).attr('data-visual-config-type');
                    let config_value = null;
                    let visual_config_value_id = null;
                    let analysis_visual_config_id = $(this).attr('data-analysis-visual-config-id');
                    if (config_type == "input_string" || config_type == "input_number") {
                        config_value = $(this).val();
                    } else if (config_type == "toggle") {
                        config_value = $(this).is(":checked");
                    } else if (config_type == "selection_string" || config_type == "selection_number") {
                        config_value = $(this).val();
                        visual_config_value_id = $(`#${$(this).attr("id")} option:selected`).attr('data-visual-config-value-id');
                    }
                    config_values.push({
                        'id': analysis_visual_config_id != 'null' ? parseInt(analysis_visual_config_id) : null,
                        'analysis_id': self.selectedAnalysis,
                        'visual_config_id': parseInt($(this).attr('data-visual-config-id')),
                        'visual_config_value_id': visual_config_value_id != null ? parseInt(visual_config_value_id) : null,
                        'string_value': String(config_value),
                    })
                })

                self._rpc({
                    model: 'izi.analysis',
                    method: 'save_analysis_visual_config',
                    args: [[self.selectedAnalysis], config_values],
                }).then(function (result) {
                    self._renderVisual();
                    self._renderVisualConfigs();
                })
            }
        },

        _onChangeLimit: function () {
            var self = this;
            if (self.selectedAnalysis) {
                self.changeLimit = parseInt(self.$changeLimit.val());
                var data = {
                    'limit': self.changeLimit,
                }
                self._rpc({
                    model: 'izi.analysis',
                    method: 'write',
                    args: [self.selectedAnalysis, data],
                }).then(function (result) {
                    self._loadAnalysisInfo();
                    self._renderVisual();
                })
            }
        },

        _getVisualConfigValues: function () {
            var self = this;
            let visual_config_values = {}
            $('.izi_select_visual_config_container .izi_visual_config').each(function () {
                let config_type = $(this).attr('data-visual-config-type');
                let config_value = null;
                if (config_type == "input_string") {
                    config_value = $(this).val();
                } else if (config_type == "input_number") {
                    config_value = parseInt($(this).val());
                } else if (config_type == "toggle") {
                    config_value = $(this).is(":checked");
                } else if (config_type == "selection_string") {
                    config_value = $(this).val();
                } else if (config_type == "selection_number") {
                    config_value = parseInt($(this).val());
                }
                visual_config_values[$(this).attr('data-visual-config')] = config_value;
            })
            return visual_config_values;
        },

        _loadDashboards: function() {
            var self = this;
            self.$selectDashboard = new IZIAutocomplete(self, {
                'elm': self.$('#izi_select2_dashboard'),
                'multiple': false,
                'placeholder': 'Select Dashboard',
                'minimumInput': false,
                'params':  {
                    'model': 'izi.dashboard',
                    'textField': 'name',
                    'fields': ['id', 'name'],
                    'domain': [],
                    'limit': 10,
                },
                'textField': 'name',
                'onChange': function(id, name) {
                    self.selectedDashboard = id;
                    self.selectedDashboardName = name;
                },
            })
        },

        _checkActionContext: function() {
            var self = this;
            if (self.props) {
                for (const key in self.props) {
                    if (self.props[key] && self.props[key].context && self.props[key].context.analysis_id) {
                        self.selectedAnalysis = self.props[key].context.analysis_id;
                        self._rpc({
                            model: 'izi.analysis',
                            method: 'search_read',
                            args: [[['id', '=', self.selectedAnalysis]], ['id', 'name', 'table_id', 'visual_type_id']],
                        }).then(function (results) {
                            // console.log('Check Actions Context', results);
                            if (results && results.length) {
                                var result = results[0];
                                if (result.id && result.name && result.table_id && result.table_id.length && result.visual_type_id && result.visual_type_id.length) {
                                    self._selectAnalysis(result.id, result.name, result.table_id[1], result.visual_type_id[1]);
                                }
                            }
                        })
                    } 
                }
            }
        }

    });

    return IZIConfigAnalysis;
});
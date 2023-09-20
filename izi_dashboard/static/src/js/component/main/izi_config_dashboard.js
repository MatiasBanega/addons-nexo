odoo.define('izi_dashboard.IZIConfigDashboard', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var core = require('web.core');
    var _t = core._t;
    var datepicker = require('web.datepicker');
    
    var IZISelectDashboard = require('izi_dashboard.IZISelectDashboard');
    var IZIAddAnalysis = require('izi_dashboard.IZIAddAnalysis');
    var IZIAutocomplete = require('izi_dashboard.IZIAutocomplete');
    var IZIConfigDashboard = Widget.extend({
        template: 'IZIConfigDashboard',
        events: {
            'click .izi_edit_layout': '_onClickEditLayout',
            'click .izi_auto_layout': '_onClickAutoLayout',
            'click .izi_save_layout': '_onClickSaveLayout',
            'click .izi_select_dashboard': '_onClickSelectDashboard',
            'click .izi_edit_dashboard_input': '_onClickDashboardInput',
            'click .izi_edit_dashboard_button': '_onClickEditDashboard',
            'click .izi_save_dashboard_button': '_onClickSaveDashboard',
            'click .izi_delete_dashboard': '_onClickDeleteDashboard',
            'click .izi_add_analysis': '_onClickAddAnalysis',
            'click #izi_export_capture': '_onClickExportCapture',
            'click .izi_select_theme': '_onClickSelectTheme',
            'click .izi_select_date_format': '_onClickSelectDateFormat',
        },

        /**
         * @override
         */
        init: function (parent, $viewDashboard) {
            var self = this;
            this._super.apply(this, arguments);
            self.parent = parent;
            if (parent.props) self.props = parent.props;
            self.$viewDashboard = $viewDashboard;
            self.$selectDashboard;
            self.selectedDashboard;
            self.selectedDashboardName;
            self.selectedDashboardWriteDate;
            self.selectedDashboardThemeName;
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

        render: function(){
            var self = this;
        },

        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            
            self.$selectDashboard = self.$('.izi_select_dashboard');
            self.$titleDashboard = self.$('.izi_title_dashboard');
            self.$configDashboardContainer = self.$('.izi_config_dashboard_button_container');
            self.$editDashboard = self.$('.izi_edit_dashboard');
            self.$inputDashboard = self.$('.izi_edit_dashboard_input');
            self.$btnDashboardEdit = self.$('.izi_edit_dashboard_button');
            self.$btnDashboardSave = self.$('.izi_save_dashboard_button');
            self.$themeContainer = self.$('.izi_select_theme_container');
            self.$btnExportCapture = self.$('#izi_export_capture');
            self.$btnExportLoading = self.$('#izi_export_capture_loading');
            self.$btnEditLayout = self.$('.izi_edit_layout');
            self.$btnSaveLayout = self.$('.izi_save_layout');
            self.$btnAutoLayout = self.$('.izi_auto_layout');
            // Filter
            self.filterDateRange = {};
            self.filterDateRange.elm = self.$('#izi_dashboard_filter_date_range');
            self.filterDateRange.values = [null, null];
            self.filterDateFormat = {};
            self.filterDateFormat.elm = self.$('#izi_dashboard_filter_date_format');
            self.filterDateFormat.values = null;
            
            // Load
            self._loadThemes();
            self._checkActionContext();
            self._initDashboard();
            self._initDashboardFilter();
        },

        /**
         * Private Method
         */
        _loadThemes: function (ev) {
            var self = this;
            self.$themeContainer.empty();
            self._rpc({
                model: 'izi.dashboard.theme',
                method: 'search_read',
                args: [[], ['id', 'name'],],
                kwargs: {
                    order: [{ name: 'name', asc: true }],
                },
            }).then(function (results) {
                results.forEach(res => {
                    self.$themeContainer.append(`<a theme-id="${res.id}" class="dropdown-item izi_select_theme izi_select_theme_${res.name}">${res.name}</a>`);
                });
            });
        },

        _checkActionContext: function() {
            var self = this;
            if (self.props) {
                for (const key in self.props) {
                    if (self.props[key] && self.props[key].context && self.props[key].context.dashboard_id) {
                        self.selectedDashboard = self.props[key].context.dashboard_id;
                    } 
                }
            }
        },

        _initDashboard: function (ev) {
            var self = this;
            var domain = []
            if (self.selectedDashboard) {
                domain = [['id', '=', self.selectedDashboard]]
            }
            self._rpc({
                model: 'izi.dashboard',
                method: 'search_read',
                args: [domain, ['id', 'name', 'write_date', 'theme_name', 'date_format', 'start_date', 'end_date']],
            }).then(function (results) {
                if (results.length > 0) {
                    self._selectDashboard(results[0].id, results[0].name, results[0].write_date, results[0].theme_name, results[0].date_format, results[0].start_date, results[0].end_date);
                } else {
                    if (self.$viewDashboard.$grid) {
                        self.$viewDashboard.$grid.removeAll();
                    }
                    self.$configDashboardContainer.hide();
                    self.$titleDashboard.text('Select Dashboard');
                    self.$selectDashboard.find('.izi_subtitle').text('Click to select existing dashboard or create a new one');
                }
            })
            self._rpc({
                model: 'izi.dashboard',
                method: 'get_user_groups',
            }).then(function(result){
                let user_group_dashboard = result['user_group_dashboard'] ?? '';
                let user_group_analysis = result['user_group_analysis'] ?? '';

                if (user_group_dashboard == 'User' && user_group_analysis != '') {
                    $('.izi_add_analysis').hide();
                    $('.izi_edit_layout').hide();
                    $('.izi_delete_dashboard').hide();
                } else {
                    $('.izi_add_analysis').show();
                    $('.izi_edit_layout').show();
                    $('.izi_delete_dashboard').show();
                }
            })

        },

        _initDashboardFilter: function() {
            var self = this;
            // Date Range
            self.filterDateRange.elm.find('.izi_dashboard_filter_content').empty();
            self.filterDateRange.values = [null, null];
            var $dateFrom = new datepicker.DateWidget(self);
            $dateFrom.appendTo(self.filterDateRange.elm.find('.izi_dashboard_filter_content')).then((function () {
                // $dateFrom.setValue(moment(this.value));
                $dateFrom.$el.find('input').addClass('izi_input').attr('placeholder', 'Date From');
                $dateFrom.on('datetime_changed', self, function () {
                    var newValue = $dateFrom.getValue() ? moment($dateFrom.getValue()).format('YYYY-MM-DD') : null;
                    if (self.filterDateRange.values[0] != newValue) {
                        self.filterDateRange.values[0] = newValue;
                        self._loadFilteredDashboard();
                    }
                });
            }));
            var $dateTo = new datepicker.DateWidget(self);
            $dateTo.appendTo(self.filterDateRange.elm.find('.izi_dashboard_filter_content')).then((function () {
                // $dateTo.setValue(moment(this.value));
                $dateTo.$el.find('input').addClass('izi_input').attr('placeholder', 'Date To');
                $dateTo.on('datetime_changed', self, function () {
                    var newValue = $dateTo.getValue() ? moment($dateTo.getValue()).format('YYYY-MM-DD') : null;
                    if (self.filterDateRange.values[1] != newValue) {
                        self.filterDateRange.values[1] = newValue;
                        self._loadFilteredDashboard();
                    }
                });
            }));
        },

        _onClickSelectDateFormat: function(ev) {
            var self = this;
            self.filterDateFormat.values = $(ev.currentTarget).data('date_format');
            var text = $(ev.currentTarget).text();
            self.filterDateFormat.elm.find('.izi_dashboard_filter_content .dropdown-toggle').text(text);
            if (self.filterDateFormat.values == 'custom') {
                self.filterDateRange.elm.show();
            } else {
                self.filterDateRange.elm.hide();
                self._loadFilteredDashboard();
            }
        },
        
        _loadFilteredDashboard: function() {
            var self = this;
            var filters = {};
            if (self.filterDateFormat.values) {
                filters.date_format = self.filterDateFormat.values;
                if (self.filterDateFormat.values == 'custom') {
                    filters.date_range = self.filterDateRange.values;
                }
            }
            if (self.selectedDashboard && self.$viewDashboard) {
                self.$viewDashboard._setDashboard(self.selectedDashboard);
                self.$viewDashboard._loadDashboard(filters);
            }
        },

        _onClickSelectTheme: function (ev) {
            var self = this;
            var theme_id = parseInt($(ev.currentTarget).attr('theme-id'));
            var theme_name = $(ev.currentTarget).text();
            if (theme_id && theme_name) {
                new swal({
                    title: "Change confirmation",
                    text: `
                        Do you confirm to change the dashboard theme?
                    `,
                    icon: "warning",
                    showCancelButton: true,
                    confirmButtonText: 'Yes',
                    heightAuto : false,
                }).then((result) => {
                    if (result.isConfirmed) {
                        var data = {
                            'theme_id': theme_id,
                        }
                        self._rpc({
                            model: 'izi.dashboard',
                            method: 'write',
                            args: [self.selectedDashboard, data],
                        }).then(function (result) {
                            new swal('Success', `Dashboard theme has been changed successfully`, 'success');
                            amChartsTheme.applyTheme(theme_name);
                            $(".dropdown-item.izi_select_theme").removeClass("active");
                            $(ev.currentTarget).addClass("active");

                            if (self.selectedDashboard && self.$viewDashboard) {
                                self._loadFilteredDashboard()
                            }
                        });
                    }
                });
            }
        },

        _onClickEditLayout: function(ev) {
            var self = this;
            self.$btnEditLayout.hide();
            self.$btnSaveLayout.show();
            self.$btnAutoLayout.show();
            self.$viewDashboard.$grid.enable(); //enable widgets moving/resizing.
        },
        _onClickAutoLayout: function(ev) {
            var self = this;
            self.$viewDashboard.$grid.float(false);
            self.$viewDashboard.$grid.compact();
            self.$viewDashboard.$grid.float(true);
        },

        _onClickSaveLayout: function(ev) {
            var self = this;
            if (self.$viewDashboard && self.$viewDashboard.$grid) {
                var layout = self.$viewDashboard.$grid.save(false)
                if (layout) {
                    self._rpc({
                        model: 'izi.dashboard.block',
                        method: 'ui_save_layout',
                        args: [layout],
                    }).then(function (result) {
                        if (result.status == 200) {
                            self.$btnEditLayout.show();
                            self.$btnSaveLayout.hide();
                            self.$btnAutoLayout.hide();
                            self.$viewDashboard.$grid.disable(); //Disables widgets moving/resizing.
                            self._loadFilteredDashboard();
                            new swal('Success', `Dashboard layout has been saved successfully.`, 'success');
                        }
                    })
                }
                
            }
        },

        _onClickSelectDashboard: function (ev) {
            var self = this;
            // Add Dialog
            var $select = new IZISelectDashboard(self)
            $select.appendTo($('body'));
        },

        _selectDashboard: function (id, name, write_date, theme_name, date_format, start_date, end_date) {
            var self = this;
            self.selectedDashboard = id;
            self.selectedDashboardName = name;
            self.selectedDashboardWriteDate = write_date;
            self.selectedDashboardThemeName = theme_name;
            self.$titleDashboard.text(name);
            if (date_format) {
                self.filterDateFormat.values = date_format;
                var text = self.filterDateFormat.elm.find(`[data-date_format="${date_format}"]`).text()
                self.filterDateFormat.elm.find('.izi_dashboard_filter_content .dropdown-toggle').text(text);
            }
            if (date_format == 'custom' && (start_date || end_date)) {
                self.filterDateRange.values = [start_date, end_date]
            }
            self.$selectDashboard.find('.izi_subtitle').text('Last Updated On ' + moment(write_date).format('LLL'));
            if (self.$viewDashboard) {  
                self.$configDashboardContainer.show();
                self._loadFilteredDashboard();
                $(".dropdown-item.izi_select_theme").removeClass("active");
                self.$(`.izi_select_theme_${theme_name}`).addClass("active");
                amChartsTheme.applyTheme(theme_name);
            }
        },

        _onClickEditDashboard: function(ev) {
            var self = this;
            ev.stopPropagation();
            if (self.selectedDashboard && self.$btnDashboardEdit.is(":visible")) {
                self.$titleDashboard.hide();
                self.$inputDashboard.val(self.$titleDashboard.text());
                self.$editDashboard.show();
                self.$btnDashboardEdit.hide();
                self.$btnDashboardSave.show();
            }
        },

        _onClickSaveDashboard: function(ev) {
            var self = this;
            ev.stopPropagation();
            var name = self.$inputDashboard.val();
            if (self.selectedDashboard && name) {
                new swal({
                    title: "Edit Confirmation",
                    text: `
                        Do you confirm to change the dashboard information?
                    `,
                    icon: "warning",
                    showCancelButton: true,
                    confirmButtonText: 'Yes',
                    heightAuto : false,
                }).then((result) => {
                    if (result.isConfirmed) {
                        var data = {
                            'name': name,
                        }
                        self._rpc({
                            model: 'izi.dashboard',
                            method: 'write',
                            args: [self.selectedDashboard, data],
                        }).then(function (result) {
                            new swal('Success', `Dashboard has been saved successfully`, 'success');
                            self.$titleDashboard.text(name);
                            self.$titleDashboard.show();
                            self.$editDashboard.hide();
                            self.$btnDashboardEdit.show();
                            self.$btnDashboardSave.hide();
                        });
                    }
                });
            }
        },

        _onClickDeleteDashboard: function(ev) {
            var self = this;
            ev.stopPropagation();
            if (self.selectedDashboard) {
                new swal({
                    title: "Delete Confirmation",
                    text: `
                        Do you confirm to delete the dashboard ?
                    `,
                    icon: "warning",
                    showCancelButton: true,
                    confirmButtonText: 'Yes',
                    heightAuto : false,
                }).then((result) => {
                    if (result.isConfirmed) {
                        var data = {
                            'name': name,
                        }
                        self._rpc({
                            model: 'izi.dashboard',
                            method: 'unlink',
                            args: [self.selectedDashboard],
                        }).then(function (result) {
                            new swal('Success', `Dashboard has been deleted successfully`, 'success');
                            self._initDashboard();
                        });
                    }
                });
            }
        },

        _onClickAddAnalysis: function (ev) {
            var self = this;
            ev.stopPropagation();
            if (self.selectedDashboard) {
                var self = this;
                // Add Dialog
                var $select = new IZIAddAnalysis(self)
                $select.appendTo($('body'));
            }
        },
        
        _onClickExportCapture: function (ev) {
            var self = this;
            self.$btnExportCapture.hide();
            self.$btnExportLoading.show();

            ev.stopPropagation();
            if (self.selectedDashboard) {
                // self.$captureContainer.on('click', function(){
                var btn = $(self).button('loading');
                html2canvas(document.querySelector('.izi_view_dashboard'), {useCORS: true, allowTaint: false}).then(function(canvas){
                    window.jsPDF = window.jspdf.jsPDF;
                    var doc = new jsPDF("p", "mm", "a4");
                    var img = canvas.toDataURL("image/jpeg", 0.90);
                    var imgProps= doc.getImageProperties(img);
                    var pageHeight = 295;
                    var width = doc.internal.pageSize.getWidth();
                    var height = (imgProps.height * width) / imgProps.width;
                    var heightLeft = height;
                    var position = 0;
                    
                    doc.addImage(img,'JPEG', 0, 0, width, height, 'FAST');
                    heightLeft -= pageHeight;
                    while (heightLeft >= 0) {
                        position = heightLeft - height;
                        doc.addPage();
                        doc.addImage(img, 'JPEG', 0, position,  width, height, 'FAST');
                        heightLeft -= pageHeight;
                    };
                    doc.save(self.$titleDashboard[0].innerHTML + '.pdf');
                    new swal('Success', `Dashboard has been Captured.`, 'success');
                    btn.button('reset');

                    self.$btnExportCapture.show();
                    self.$btnExportLoading.hide();
                });
                // });
            } 
        },

        _onClickDashboardInput: function(ev) {
            var self = this;
            ev.stopPropagation();
        },
    });

    return IZIConfigDashboard;
});
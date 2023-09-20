odoo.define('izi_dashboard.IZIAutocomplete', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var view_dialogs = require('web.view_dialogs');
    var QWeb = core.qweb;
    var _t = core._t;
    
    class IZIAutocomplete {
        constructor(parent, args) {
            var self = this;
            self.parent = parent;
            self.elm = args.elm;
            self.multiple = args.multiple;
            self.placeholder = args.placeholder;
            self.params = args.params;
            self.initData = args.initData || (args.multiple ? null : {});
            self.formatFunc = function format(item) { 
                return item[self.params.textField || 'name']; 
            }
            self.onChange = args.onChange;
            self.selectedId;
            self.selectedText = '';
            if (args.minimumInput)
                self.minimumInputLength = 1;
            else
                self.minimumInputLength = 0;
            self.init();
            self.initOnChange();
        }
        set(key, value) {
            var self = this;
            self[key] = value;
        }
        setDomain(domain) {
            var self = this;
            self.params.domain = domain;
            self.init();
        }
        destroy() {
            var self = this;
            self.elm.select2('destroy');
        }
        init(){
            var self = this;
            var typingTimer;
            var loadingRPC = false;
            self.elm.select2({
                multiple: self.multiple,
                allowClear: true, 
                tokenSeparators: [',', ' '], 
                minimumResultsForSearch: 10, 
                placeholder: self.placeholder,
                minimumInputLength: self.minimumInputLength,
                query: function (query) {
                    var data = {results: []};
                    var domain = [[self.params.textField, 'ilike', query.term]];
                    if (Array.isArray(self.params.domain)  && self.params.domain.length)
                        Array.prototype.push.apply(domain, self.params.domain)
                    clearTimeout(typingTimer);
                    if (query && !loadingRPC) {
                        typingTimer = setTimeout(function() {
                            //do something
                            loadingRPC = true;
                            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                                model: self.params.model,
                                method: 'search_read',
                                args: [domain, self.params.fields],
                                limit: self.params.limit,
                                kwargs: {},
                            }).then(function (results) {
                                // console.log('Query', query.term);
                                // console.log('RPC', results);
                                query.callback({results: results});
                                loadingRPC = false;
                            });
                        }, 500);
                    }
                    
                },
                formatSelection: self.formatFunc,
                formatResult: self.formatFunc,
                initSelection : function (element, callback) {
                    callback(self.initData);
                }
            })
        }
        initOnChange() {
            var self = this;
            self.elm.select2('val', []).on("change", function (e) {
                if (e.added) {
                    self.selectedText = e.added[self.params.textField];
                }
                self.selectedId = parseInt(e.val);
                if (!self.selectedId) {
                    self.selectedText = '';
                }
                self.onChange(self.selectedId, self.selectedText);
            })
        }
    }
    return IZIAutocomplete;
})

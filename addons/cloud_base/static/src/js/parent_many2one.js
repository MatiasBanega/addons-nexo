/** @odoo-module **/

import AbstractField from "web.AbstractField";
import fieldRegistry from "web.field_registry";
import ModelFieldSelector from "web.ModelFieldSelector";

const parentRuleMany2one = AbstractField.extend({
    supportedFieldTypes: ['char'],
    resetOnAnyFieldChange: true,
    /**
     * Re-write to apply own fields selector options
     */
    init: function (parent, name, record, options) {
        this._super.apply(this, arguments);
        this.options = _.extend({
            readonly: false,
            debugMode: true,
            filter: this._filterByMany2one,
        }, options || {});
        this.options.filters = {type: "many2one"};
        this.readonly = false;
    },
    /*
     * Re-write to initiate ModelFieldSelector
    */
    _renderEdit: function () {
        if (this.recordData.model) {
            this.fieldSelector = new ModelFieldSelector(
                this,
                this.recordData.model,
                this.value && this.value !== undefined ? this.value.toString().split(".") : [],
                this.options
            );
            var self = this;
            this.fieldSelector.appendTo($("<div/>")).then( function () {
                self.$el.html(self.fieldSelector.$el[0]);
            });
        };
    },
    /*
     * Re-write to parse pure char value
    */
    _renderReadonly: function () {
        this.$el.html(this.value);
    },
    /*
     * Re-write to save field selector final choice
    */
    commitChanges: function () {
        var finValue = false;
        if (this.fieldSelector && this.fieldSelector.chain && this.fieldSelector.chain.length != 0) {
            finValue = this.fieldSelector.chain.join(".")
        };
        this._setValue(finValue);
    },
    /*
     * The method used to filter fields for our expression
    */
    _filterByMany2one: function(f) {
        return f.type == "many2one";
    }
});


fieldRegistry.add("parentRuleMany2one", parentRuleMany2one);

export default parentRuleMany2one;

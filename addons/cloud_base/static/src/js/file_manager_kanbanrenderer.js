/** @odoo-module **/

import fileKanbanRecord from "@cloud_base/js/file_manager_kanbanrecord";
import KanbanRenderer from "web.KanbanRenderer";

const fileKanbanRenderer = KanbanRenderer.extend({
    config: _.extend({}, KanbanRenderer.prototype.config, {KanbanRecord: fileKanbanRecord}),
    /**
    * Re-write to keep selected files when switching between pages and filters
    */
    updateSelection: function (selectedRecords) {
        _.each(this.widgets, function (widget) {
            if (typeof widget._updateRecordView === 'function') {
                var selected = _.contains(selectedRecords, widget.id);
                widget._updateRecordView(selected);
            }
            else {
                _.each(widget.records, function (widg) {
                    var selected = _.contains(selectedRecords, widg.id);
                    widg._updateRecordView(selected);
                });
            }
        });
    },
});

export default fileKanbanRenderer;

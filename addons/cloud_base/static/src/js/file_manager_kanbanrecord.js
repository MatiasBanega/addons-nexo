/** @odoo-module **/

import KanbanRecord from "web.KanbanRecord";

const fileKanbanRecord = KanbanRecord.extend({
    events: _.extend({}, KanbanRecord.prototype.events, {
        "click .file_select": "_fileSelect",
        "click .o_kanban_image": "_realOpenRecord",
    }),
    /** 
    * The method to pass selection to the controller
    */
    _updateSelect: function (event, selected) {
        this.trigger_up("select_record", {
            originalEvent: event,
            resID: this.id,
            selected: selected,
        });
    },
    /** 
    * The method to mark the file selected / disselected in the interface
    */
    _updateRecordView: function (select) {
        var kanbanCard = this.$el,
            checkBox = this.$el.find(".file_select");
        if (select) {
            checkBox.removeClass("fa-square-o");
            checkBox.addClass("fa-check-square-o");
            kanbanCard.addClass("file_kanabanselected");
        }
        else {
            checkBox.removeClass("fa-check-square-o");
            checkBox.addClass("fa-square-o");
            kanbanCard.removeClass("file_kanabanselected");
        };
    },
    /** 
    * The method to add to / remove from selection
    */
    _fileSelect: function (event) {
        event.preventDefault();
        event.stopPropagation();
        var checkBox = this.$el.find(".file_select");
        if (checkBox.hasClass("fa-square-o")) {
            this._updateRecordView(true)
            this._updateSelect(event, true);
        }
        else {
            this._updateRecordView(false);
            this._updateSelect(event, false);
        }
    },    	
    /** 
    * Re-write to make selection instead of opening a record
    */
    _openRecord: function (real) {
        if (!real) {this.$(".file_select").click()}
        else {this._super.apply(this, arguments)};
    },
    /** 
    * When clicked on image > open form view
    */
    _realOpenRecord: function (event) {
        this._openRecord(true);
    },
});

export default fileKanbanRecord

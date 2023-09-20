/** @odoo-module **/

import ListController from "web.ListController"; 

const noArchiveController = ListController.extend({
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.archiveEnabled = false;
    },
});

export default noArchiveController;

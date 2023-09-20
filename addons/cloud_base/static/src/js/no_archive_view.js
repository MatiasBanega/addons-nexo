/** @odoo-module **/

import noArchiveController from "@cloud_base/js/no_archive_controller";
import ListView from "web.ListView";
import viewRegistry from "web.view_registry";

const noArchiveView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: noArchiveController,
    }),
});

viewRegistry.add("no_archive_tree", noArchiveView);

export default noArchiveView;

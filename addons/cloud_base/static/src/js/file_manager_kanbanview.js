/** @odoo-module **/

import fileKanbanController from "@cloud_base/js/file_manager_kanbancontroller";
import fileKanbanModel from "@cloud_base/js/file_manager_kanbanmodel";
import fileKanbanRenderer from "@cloud_base/js/file_manager_kanbanrenderer";
import KanbanView from "web.KanbanView";
import viewRegistry from "web.view_registry";
import { _lt } from "web.core";

const fileKanbanView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Controller: fileKanbanController,
        Model: fileKanbanModel,
        Renderer: fileKanbanRenderer,
    }),
    display_name: _lt('Files Manager'),
    groupable: false,
});

viewRegistry.add("cloud_base_kanban", fileKanbanView);

export default fileKanbanView;

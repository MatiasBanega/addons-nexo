/** @odoo-module **/

import AbstractField from "web.AbstractField";
import fieldRegistry from "web.field_registry";
import dialogs from "web.view_dialogs";
import { qweb, _lt } from "web.core"; 


const jsTreeWidget = AbstractField.extend({
    supportedFieldTypes: ["char"],
    resetOnAnyFieldChange: false,
    jsLibs: ["/cloud_base/static/lib/jstree/jstree.js",],
    cssLibs: ["/cloud_base/static/lib/jstree/themes/default/style.css",],
    events: _.extend({}, AbstractField.prototype.events, {
        "click #createJsTreeNode": "_onAddNode",
        "click #createJsTreeFile": "_uploadFile",
        "click #editJsTreeNode": "_onEditNode",
        "click #deleteJsTreeNode": "_onDeleteNode",
    }),
    /*
     * Re-write to parse jstree lib
    */
    _renderEdit: function () {
        var self = this;
        var template = qweb.render("jsTreeWidget", {"mode": self.mode});
        self.$el.html(template);
        var cur_data = []
        if (self.value) {cur_data = eval(self.value)};
        var ref = self.$("#jsTreeContainer").jstree({
            "core" : {
                "check_callback" : function (operation, node, node_parent, node_position, more) {
                    if (operation === "move_node" && node_parent && node_parent.icon == "fa fa-file-o") {
                        // forbid assigning attachment node as parent
                        return false;
                    };
                    return true;
                },
                "data": cur_data,
            },
            "plugins" : [
                "dnd",
                "state",
                "unique",
                "contextmenu",
            ],
            "contextmenu": {
                "items": function($node) {
                    var tree = $("#jsTreeContainer").jstree(true);
                    return {
                        "Create": {
                            "separator_before": false,
                            "separator_after": false,
                            "label": _lt("Create"),
                            "action": function (obj) {
                                if ($node.icon == "fa fa-file-o") {
                                    self._uploadFile(obj, tree.get_node($node.parent));
                                }
                                else {
                                    $node = tree.create_node($node);
                                    tree.edit($node);
                                };
                            }
                        },
                        "Edit": {
                            "separator_before": false,
                            "separator_after": false,
                            "label": _lt("Edit"),
                            "action": function (obj) {
                                if ($node.icon == "fa fa-file-o") {
                                    self._uploadFile(obj, tree.get_node($node.parent), $node);
                                }
                                else {
                                    tree.edit($node);
                                };
                            }
                        },
                        "Delete": {
                            "separator_before": false,
                            "separator_after": false,
                            "label": _lt("Delete"),
                            "action": function (obj) {
                                tree.delete_node($node);
                            }
                        },
                        "Upload": {
                            "separator_before": true,
                            "separator_after": false,
                            "label": _lt("Upload File"),
                            "action": function (obj) {
                                if ($node.icon == "fa fa-file-o") {
                                    self._uploadFile(obj, tree.get_node($node.parent));
                                }
                                else {
                                    self._uploadFile(obj);
                                };
                            }
                        },
                    }
                },
            },                
        });
        // Manage any change to register it
        self.$("#jsTreeContainer").on("rename_node.jstree", self, function (event, data) {
            // when created, a node is always renamed
            self._onChangeTree(event, data);
        });
        self.$("#jsTreeContainer").on("move_node.jstree", self, function (event, data) {
            self._onChangeTree(event, data);
        });
        self.$("#jsTreeContainer").on("delete_node.jstree", self, function (event, data) {
            self._onChangeTree(event, data);
        });
        self.$("#jsTreeContainer").on("copy_node.jstree", self, function (event, data) {
            self._onChangeTree(event, data);
        });
    },
    /*
     * Re-write to parse jstree lib
    */
    _renderReadonly: function () {
        var self = this;
        var template = qweb.render("jsTreeWidget", {"mode": self.mode});
        self.$el.html(template);
        var cur_data = []
        if (self.value) {
            cur_data = eval(self.value)
        };
        var ref = self.$("#jsTreeContainer").jstree({
            "core" : {
                "themes" : { "stripes" : false },
                "data": cur_data,
            },
        });
    },
    /*
     * The method to add a new node
    */
    _onAddNode: function(event) {
        var self = this;
        var ref = self.$("#jsTreeContainer").jstree(true),
            sel = ref.get_selected();
        sel = ref.create_node("#");
        if(sel) {ref.edit(sel)};
    },
    /*
     * The method to edit a node
    */
    _onEditNode: function(event) {
        var self = this;
        var ref = self.$("#jsTreeContainer").jstree(true),
            sel = ref.get_selected();
        if(!sel.length) { return false; }
        sel = sel[0];
        ref.edit(sel);
    },
    /*
     * The method to delete a node
    */
    _onDeleteNode: function(event) {
        var self = this;
        var ref = self.$("#jsTreeContainer").jstree(true),
            sel = ref.get_selected();
        if(!sel.length) { return false; }
        ref.delete_node(sel);
    },
    /*
     * The method to apply changes
    */
    _onChangeTree: function(event, data) {
        var self = this;
        var ref = self.$("#jsTreeContainer").jstree(true);
        var cur_data = JSON.stringify(ref.get_json());
        self._setValue(cur_data);
    },
    /*
     * The method to open new attachment form and generate file node based on its result
    */
    async _uploadFile(data, $node, existing) {
        var self = this;
        var view_id = await this._rpc({
            model: "ir.attachment",
            method: "return_js_upload_form",
            args: [],
        });
        var resID = false;
        if (existing) {resID = parseInt(existing.id)};
        var onSaved = function(record) {
            var ref = self.$("#jsTreeContainer").jstree(data.reference),
                obj = $node || ref.get_node(data.reference);
            if (existing) {
                ref.set_text(existing, record.data.name);
                self._onChangeTree();
            }
            else {
                var new_node_vals = {
                    "text": record.data.name,
                    "icon": "fa fa-file-o",
                    "id": record.data.id.toString(),
                };
                ref.create_node(obj || "#", new_node_vals, "last", function (new_node) {
                    ref.open_node(obj);
                    self._onChangeTree();
                });
            }
        };
        new dialogs.FormViewDialog(self, {
            res_model: "ir.attachment",
            title: _lt("Upload attachment"),
            view_id: view_id,
            res_id: resID,
            readonly: false,
            shouldSaveLocally: false,
            on_saved: onSaved,
        }).open();
    },
});

fieldRegistry.add("jsTreeWidget", jsTreeWidget);

export default jsTreeWidget;

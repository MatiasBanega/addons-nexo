/** @odoo-module **/
    
import { registerMessagingComponent } from '@mail/utils/messaging_component';
import { ComponentAdapter } from "web.OwlCompatibility";
import dialogs from "web.view_dialogs";

const { Component } = owl;

class FormViewDialogComponentAdapter extends ComponentAdapter {
    /**
     * Special owl-compatibility class to itnroduce form view dialog as a component
     */
    renderWidget() {
        return this.willStart();
    }
};

export class CloudFolderTree extends Component {
    /**
     * @override to load js tree lib
     */
    async willStart() {
        await this.env.services.ajax.loadLibs({
            "jsLibs": ["/cloud_base/static/lib/jstree/jstree.js"],
            "cssLibs": [
                "/cloud_base/static/lib/jstree/themes/default/style.css",
                "/cloud_base/static/src/css/jstree.css",
            ],
        }, {}, "");
    }
    /**
     * @override to parse js tree of folders
     */
    mounted() {
        this._renderFoldersTree();
    }
    /**
     * @returns Object - dict of linked clouds folder with recursive children
     */
    get cloudFolders() {
        return this.props.cloudFolders;
    }
    /**
     * @returns Boolean - whether current user may manage folders
     */
    get createRight() {
        return this.props.createRight;
    }
    /**
     * @returns String - js tree key to save state
     */
    get jstreeKey(){
        return this.props.jstreeKey;
    }
    /**
     * @returns Boolean - whether it is possible to create the first level folders
     */
    get rootCreateAllowed(){
        return this.props.rootCreateAllowed;
    }
    /**
     * @returns Object - parent UI which should be updated in case of checks, for example
     * if we got from parent component, we use that. Otherwise, parentView should be passed
     */
    get parentUI(){
        var parentView = this.props.parentView;
        if (this.__owl__ && this.__owl__.parent) {
            parentView = this.__owl__.parent;
        };
        return parentView
    }
    /**
     * @private
     * the method to mount js tree of the current folders
     */        
    _renderFoldersTree() {
        var self = this,
            jstreeEl =  $(document.querySelector('#cloud_folders'));
        jstreeEl.jstree('destroy'); // Destroy previous tree and render a new one
        var jsTreeOptions = {
            'core' : {
                'check_callback' : function (operation, node, node_parent, node_position, more) {
                    if (operation === "move_node") {
                        if (!node_parent || !node_parent.data || !node_parent.data.edit_right) {
                            return false
                        };
                    };
                    return true
                },
                'themes': {'icons': true},
                'stripes' : true,
                'multiple' : false,
                'data': self.cloudFolders,
                'strings': {"New node": self.env._t('New Folder'),},
            },
            "plugins" : [
                "state",
                "changed",
                "search",
                "dnd",
                "contextmenu",
            ],  
            "state" : {"key" : self.jstreeKey},     
            "search": {
                "case_sensitive": false,
                "show_only_matches": true,
                "fuzzy": false,
                "show_only_matches_children": true,
            }, 
            "dnd": {
                "is_draggable" : function(node) {
                    if (!node[0].data.edit_right || node[0].data.rule_related) {
                        return false;
                    }
                    return true;
                }                    
            },
            "contextmenu": {
                "select_node": false,
                "items": function($node) {
                    var tree = jstreeEl.jstree(true);
                    var items = {};
                    if ($node.data) {
                        items.downloadZip = {
                            "separator_before": false,
                            "separator_after": false,
                            "label": self.env._t("Download as archive"),
                            "action": function (obj) {
                                window.location = "/cloud_base/folder_upload/" + $node.id;
                            }
                        };                            
                    }
                    if ($node.data && $node.data.edit_right) {
                        items.createNew = {
                            "separator_before": false,
                            "separator_after": true,
                            "label": self.env._t("Create subfolder"),
                            "action": function (obj) {
                                $node = tree.create_node($node);
                                tree.edit($node);
                            }
                        };
                    };
                    if ($node.data && $node.data.url) {
                        items.openInClouds = {
                            "separator_before": false,
                            "separator_after": false,
                            "label": self.env._t("Open in clouds"),
                            "action": function (obj) {                              
                                if ($node.data && $node.data.url) {
                                    window.open($node.data.url, '_blank').focus();
                                }
                                else {
                                    alert(self.env._t("This folder is not synced yet"))
                                };
                            }
                        };
                    };
                    if ($node.data &&  !$node.data.form_root && $node.data.res_model && $node.data.res_id) {
                        items.openParentObject = {
                            "separator_before": false,
                            "separator_after": false,
                            "label": self.env._t("Open linked object"),
                            "action": function (obj) {                                  
                                self._onOpenOdooObject($node);
                            }
                        };
                    };
                    if ($node.data && ($node.data.rule_related || !$node.data.edit_right)) {
                        items.openNode = {
                            "separator_before": false,
                            "separator_after": false,
                            "label": self.env._t("Settings"),
                            "action": function (obj) {
                                var resId = parseInt($node.id);
                                self._onOpenFolder(resId);
                            }
                        };
                    }
                    else {
                        items.renameNode = {
                            "separator_before": false,
                            "separator_after": false,
                            "label": self.env._t("Rename"),
                            "action": function (obj) {
                                tree.edit($node);
                            }
                        };
                        items.editNode = {
                            "separator_before": false,
                            "separator_after": false,
                            "label": self.env._t("Edit Settings"),
                            "action": function (obj) {
                                var resId = parseInt($node.id);
                                self._onEditFolder($node, resId);
                            }
                        };
                        items.archiveNode = {
                            "separator_before": true,
                            "separator_after": false,
                            "label": self.env._t("Archive"),
                            "action": function (obj) {
                                tree.delete_node($node);
                            }
                        };
                    };                        
                    return items
                },
            },
        };  
        var ref = jstreeEl.jstree(jsTreeOptions);
        // Declare jstree events
        jstreeEl.on("rename_node.jstree", self, function (event, data) {
            // This also includes 'create' event. Since each time created, a node is updated then
            self._onUpdateNode(event, data, false);
        });
        jstreeEl.on("move_node.jstree", self, function (event, data) {
            self._onUpdateNode(event, data, true);
        });
        jstreeEl.on("delete_node.jstree", self, function (event, data) {
            self._onDeleteNode(event, data);
        });
        // Manage jstree checks ( only after restoring the tree to avoid multiple checked events)
        jstreeEl.on("state_ready.jstree", self, function (event, data) {
            self._reloadParent(true);
            jstreeEl.on("changed.jstree", self, function (event, data) {
                self._reloadParent();
            })
        });
    }
    /*
     * @private
     * The method to calculate folders domain and reload parent view 
    */        
    _reloadParent(existing_domain) {
        var domain = [],
            refT = $(document.querySelector('#cloud_folders')).jstree(true);            
        if (refT) {
            var checkedFolders = refT.get_selected(),
                checkedFolderIds = checkedFolders.map(function(item) {return parseInt(item, 10)});
            domain.push(['clouds_folder_id', 'in', checkedFolderIds]);
        };
        var checkedFolder = 0;
        if (checkedFolderIds.length > 0) {checkedFolder = checkedFolderIds[0]}
        this.parentUI._reloadBasedOnFolders(domain, existing_domain, checkedFolder);
    }
    /*
     * @private
     * @param node - jstree node
     * @param new_data - Object to be written in an updated node
     * The method to refresh updated node
    */   
    _updateNode(node, new_data) {
        var ref = $(document.querySelector('#cloud_folders')).jstree(true);
        ref.set_id(node, new_data.id);
        ref.set_text(node, new_data.text);
        ref.set_icon(node, new_data.icon);
        node.data = new_data.data;
        ref.deselect_all(true);
        ref.select_node(node);
    }
    /*
     * @private
     * The method to create a new folder without a parent
    */
    _onAddRootFolder(event) {
        var ref = $(document.querySelector('#cloud_folders')).jstree(true),
            sel = ref.create_node('#');
        if(sel) {ref.edit(sel)};
    }
    /*
     * @private
     * The method search folders in jstree
    */
    _onSearchFolder(event) {
        var searchString = $(document.querySelector('#cloud_base_folder_search'))[0].value;
        if (searchString) {
           $(document.querySelector('#cloud_folders')).jstree('search', searchString);
        }
        else {
            $(document.querySelector('#cloud_folders')).jstree('clear_search');
        }
        
    }
    /*
     * @private
     * The method to manage keyup on search input > if enter then make search
    */
    _onKeyUpSearch(event) {
        if (event.keyCode === 13) {
            this._onSearchFolder();
        };
    }
    /*
     * @private
     * The method to clear seach input and clear jstree search
    */
    _onClearSearch(even) {
        $(document.querySelector('#cloud_base_folder_search'))[0].value = "";
        $(document.querySelector('#cloud_folders')).jstree('clear_search');
    }
    /*
     * @private
     * The method to trigger update of jstree node
    */
    async _onUpdateNode(event, data, position) {
        var newNode;
        if (position) {position = parseInt(data.position)};
        if (data.node.id === parseInt(data.node.id).toString()) {
            newNode = await this.env.services.rpc({
                model: "clouds.folder",
                method: "action_js_update_node",
                args: [[parseInt(data.node.id)], data.node, position],
            });
        }
        else {
            var thisElId = data.node.id;
            newNode = await this.env.services.rpc({
                model: "clouds.folder",
                method: "action_js_create_node",
                args: [data.node],
            });
        };
        this._updateNode(data.node, newNode)
    }
    /*
     * @private
     * The method to trigger unlink of jstree node
    */
    _onDeleteNode(event, data) {
        this.env.services.rpc({
            model: "clouds.folder",
            method: "action_js_delete_node",
            args: [[parseInt(data.node.id)]],
        });
    }
    /*
     * @private
     * The method to open folder form view and save changes
    */
    async _onEditFolder($node, resID) {
        var self = this;
        var view_id = await this.env.services.rpc({
            model: "clouds.folder",
            method: "action_js_return_edit_form",
            args: [],
        });
        var onSaved = function(record) {
            self.env.services.rpc({
                model: "clouds.folder",
                method: "action_js_format_folder_for_js_tree",
                args: [[resID]],
            }).then(function (newNode) {
                self._updateNode($node, newNode);
            });
        };
        if (this.editForm) {this.editForm.destroy()};


        this.editForm = await new FormViewDialogComponentAdapter(
            this, Object.assign({
                Component: dialogs.FormViewDialog,
                params: {
                    res_model: "clouds.folder",
                    title: this.env._t("Edit Folder"),
                    view_id: view_id,
                    res_id: resID,
                    readonly: false,
                    shouldSaveLocally: false,
                    on_saved: onSaved,
                }
            }),
        );

        // this.editForm = new FormViewDialog(this, {
        //     res_model: "clouds.folder",
        //     title: this.env._t("Edit Folder"),
        //     view_id: view_id,
        //     res_id: resID,
        //     readonly: false,
        //     shouldSaveLocally: false,
        //     on_saved: onSaved,
        // })


        this.editForm.renderWidget();
        this.editForm.widget.open()
    }
    /*
     * @private
     * The method to open folder form view in readonly model
    */
    async _onOpenFolder(resID) {
        var view_id = await this.env.services.rpc({
            model: "clouds.folder",
            method: "action_js_return_edit_form",
            args: [],
        });
        if (this.readForm) {this.readForm.destroy()};
        this.readForm = await new FormViewDialogComponentAdapter(
            this, Object.assign({
                Component: dialogs.FormViewDialog,
                params: {
                    res_model: "clouds.folder",
                    title: this.env._t("Folder Settings"),
                    view_id: view_id,
                    res_id: resID,
                    readonly: true,
                    shouldSaveLocally: false,
                }
            }),
        );
        this.readForm.renderWidget();
        this.readForm.widget.open()
    }
    async _onOpenOdooObject($node) {
        if (this.odooForm) {this.odooForm.destroy()};
        this.odooForm = await new FormViewDialogComponentAdapter(
            this, Object.assign({
                Component: dialogs.FormViewDialog,
                params: {
                    res_model: $node.data.res_model,
                    res_id: $node.data.res_id,
                }
            }),
        );
        this.odooForm.renderWidget();
        this.odooForm.widget.open()                
    }
};

Object.assign(CloudFolderTree, {
    defaultProps: {
        cloudFolders: [],
        jstreeKey: "kanban_navigation",
        rootCreateAllowed: false,
        parentView: {},
    },
    props: {
        cloudFolders: {
            type: Array,
            element: Object,
        },
        jstreeKey: {
            type: String,
            optional: true,                 
        },
        rootCreateAllowed: {
            type: Boolean,
            optional: true,                 
        },
        parentView: {
            type: Object, // in case of parent component: empty dict
            optional: true,
        }
    },
    template: 'cloud.base.FolderTree',
});

registerMessagingComponent(CloudFolderTree);

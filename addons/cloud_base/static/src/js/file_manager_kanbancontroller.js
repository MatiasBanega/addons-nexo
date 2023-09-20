/** @odoo-module **/

import { getMessagingComponent } from "@mail/utils/messaging_component";
import KanbanController from "web.KanbanController"; 
import dialogs from "web.view_dialogs";
import { qweb, _lt } from "web.core"; 
import fileUploadMixin from "web.fileUploadMixin";
import CloudFolderTree from "@cloud_base/components/cloud_folder_tree/cloud_folder_tree";

const components = { CloudFolderTree };

const fileKanbanController = KanbanController.extend(fileUploadMixin, {
    buttons_template: 'fileManagerButtons',
    events: _.extend({}, KanbanController.prototype.events, {
        "click #file_manager_select_all": "_onSelectAllFound",
        "click #file_manager_clear_selection": "_onClearAllSelectedFiles",
        "click .file_manager_remove_from_selection": "_onRemoveFileSelected",
        "click #file_manager_add_file": "_onAddAttachment",
        "click #file_manager_download_btn": "_onDownloadAttachments",
        "click #file_manager_update_btn": "_onUpdateAttachments",
        "click #file_manager_unlink_btn": "_onDeleteAttachments",
    }),
    custom_events: _.extend({}, KanbanController.prototype.custom_events, {
        select_record: '_fileSelected',
    }),
    /*
     * Re-write to apply rendering params
    */
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.selectedRecords = [];
        this.navigationExist = false;
        this.attachmentsDomain = [];
        this.checkedFolder = false;
        this._fileUploads = {};
    },
    /*
     * Re-write to adapt kanban area class and render navigation
    */
    async start() {
        this.$('.o_content').addClass('d-flex');
        var res = await this._super.apply(this, arguments);
        await this._renderNavigationPanel();
        return res
    },
    /*
     * Override to render left navigation panel
    */
    async _update(state, params) {            
        var res = await this._super.apply(this, arguments);
        this.renderer.updateSelection(this.selectedRecords)
        await this._renderFileUploads();
        return res
    },
    /*
     * Override to avoid double rerendering left navigation panel
    */
    async update(params, options = {}) {
        params.attachmentsDomain = this.attachmentsDomain;
        return this._super.apply(this, arguments);
    },
    /**
     * Destroy jstree when controller is destroyed
     */
    destroy() {
        this.navigationExist = false;
        if (this.component) {
            this.component.destroy();
            this.component = undefined;
        };
        this._super(...arguments);
    },
    /*
     * Override to force reload
    */
    _reloadAfterButtonClick: function (kanbanRecord, params) {
        var self = this;
        $.when(this._super.apply(this, arguments)).then(function () {
            self.reload();
        });
    },
   /*
     * @private
     * The method to render (left) navigation panel
    */
    async _renderNavigationPanel() {
        // The method to render left navigation panel
        var scrollTop = this.$('.file_manager_navigation_panel_left').scrollTop();
        this.$('.file_manager_navigation_panel_left').remove();
        var navigationElements = {};
        var $navigationPanel = $(qweb.render('fileManagerNavigationPanel', navigationElements));
        this.$('.o_content').prepend($navigationPanel);
        await this._renderFolders();
        this.$('.file_manager_navigation_panel_left').scrollTop(scrollTop || 0);
        this.navigationExist = true;
    },
    /**
     * @private
     * The method o render right navigation panel
    */  
    async _renderRightNavigationPanel() {
        var scrollTop = this.$('.file_manager_right_navigation_panel').scrollTop();
        this.$('.file_manager_right_navigation_panel').remove();
        var selectedRecords = this.selectedRecords;
        if (selectedRecords.length) {
            var attachmentsSet = await this._rpc({
                model: "ir.attachment",
                method: 'return_selected_attachments',
                args: [this.selectedRecords],
            });
            var $navigationPanel = $(qweb.render(
                'fileManagerRightNavigationPanel', {
                    "attachments": attachmentsSet,
                    "count_files": attachmentsSet.length,
                })
            );
            this.$('.o_content').append($navigationPanel);
            this.$('.file_manager_right_navigation_panel').scrollTop(scrollTop || 0);
        };
    },
    /*
     * private
     * The method to retrieve sections for a current user
    */
    async _renderFolders() {
        if (this.component) {
            this.component.destroy();
            this.component = undefined;
        };
        var cloudFolders = await this._rpc({
            model: "clouds.folder",
            method: "action_js_return_nodes",
            args: [],
            context: this.renderer.state.context,
        });
        const CloudFolderTree = getMessagingComponent("CloudFolderTree");
        this.component = new CloudFolderTree(
            null, Object.assign({
                cloudFolders: cloudFolders,
                jstreeKey: "kanban_navigation",
                rootCreateAllowed: true,
                parentView: this,
            }),
        );
        this.component.mount(this.$("#cloud_folders_navigation")[0]);
    },
    /* 
    * @private
    * The method to trigger reload based on selected folder
    */
    _reloadBasedOnFolders(domain, existing_domain, checked_folder) {
        var self = this;
        this.checkedFolder = checked_folder;
        this.attachmentsDomain = domain;          
        var state = this.model.get(this.handle);
        if (existing_domain) {
            self.reload({"domain": state.domain});
        }
        else {
            self.reload({})
        }
    },
    /**
     * @private
     * @param {MouseEvent} event
     * The method to add an attachment to selection
    */
    _fileSelected: function(event) {
        event.stopPropagation();
        var eventData = event.data;
        var addToSelection = eventData.selected;
        if (addToSelection) {this.selectedRecords.push(eventData.resID);}
        else {this.selectedRecords = _.without(this.selectedRecords, eventData.resID);};
        this._renderRightNavigationPanel();
    },
    /**
     * The method which to block files uploading if cloud folder is not selected
    */
    updateButtons() {
        this.$buttons.find('.file_manager_add_file').prop('disabled', !this.checkedFolder);
    },
    /*
    * Override to correctly manage folder-related attachment upload
    */
    _getFileUploadRoute() {
        return '/cloud_base/upload_attachment';
    },
    /**
     * Override to pass clouds_folder_id to attachment vals
     */
    _makeFileUploadFormDataKeys() {
        return {clouds_folder_id: this.checkedFolder,};
    },
    /**
     * @private
     * @param {MouseEvent} event
     * The method to add open file dialog
    */
    _onAddAttachment(event) {
        event.stopPropagation();
        const $uploadInput = $('<input>', {
            type: 'file',
            name: 'files[]',
            multiple: 'multiple'
        });
        $uploadInput.on('change', async event => {
            await this._uploadFiles(event.target.files);
            $uploadInput.remove();
        });
        $uploadInput.click();
    },
    /**
     * @private
     * @param {MouseEvent} event
     * The method to add all attachments to selection
     * IMPORTANT: can't use res_ids since it only the first page --> so we rpc search
    */
    async _onSelectAllFound(event) {
        event.stopPropagation();
        var data = this.model.get(this.handle);
        var resIDS = await this._rpc({
            model: "ir.attachment",
            method: "action_return_all_pages_ids",
            args: [this.selectedRecords, this.model.localData[data.id].domain],
        });
        this.selectedRecords = resIDS;
        this.renderer.updateSelection(resIDS);
        this._renderRightNavigationPanel();
    },
    /**
     * @private
     * @param {MouseEvent} event
     * The method to remove all articles from selection
    */
    async _onClearAllSelectedFiles(event) {
        event.stopPropagation();
        this.selectedRecords = [];
        this.renderer.updateSelection(this.selectedRecords);
        this._renderRightNavigationPanel();
    },
     /**
     * @private
     * @param {MouseEvent} event
     * The method to this article from selection
    */
    async _onRemoveFileSelected(event) {
        event.stopPropagation();
        var resID = parseInt(event.currentTarget.id);
        this.selectedRecords = _.without(this.selectedRecords, resID);
        this.renderer.updateSelection(this.selectedRecords);
        this._renderRightNavigationPanel();
    },
    /**
     * @private
     * @param {MouseEvent} event
     * The method to download attachments: if multi - as a zip archive 
    */
    async _onDownloadAttachments(event) {
        event.stopPropagation();
        if (this.selectedRecords.length === 1) {
            window.location = "/web/content/" + this.selectedRecords[0] + "?download=true";
        } else {
            window.location = "/cloud_base/multiupload/" + this.selectedRecords.join();
        }
    },
    /**
     * @private
     * @param {MouseEvent} event
     * The method to bulk edit articles by opening a wizard
    */
    async _onUpdateAttachments(event) {
        event.stopPropagation();
        var self = this;
        var onSaved = function(record) {self.reload()};
        new dialogs.FormViewDialog(self, {
            res_model: "mass.attachment.update",
            context: {'default_attachments': self.selectedRecords.join()},
            title: _lt("Update attachments"),
            readonly: false,
            shouldSaveLocally: false,
            on_saved: onSaved,
        }).open();
    },        
    /**
     * @private
     * @param {MouseEvent} event
     * The method to bulk delete articles
    */
    async _onDeleteAttachments(event) {
        event.stopPropagation();
        await this._rpc({
            model: "ir.attachment",
            method: "unlink",
            args: [this.selectedRecords],
        });
        this.reload();
    },
});

export default fileKanbanController;

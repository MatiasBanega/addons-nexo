# -*- coding: utf-8 -*-

import json

from odoo import api, fields, models
from odoo.exceptions import UserError

FOLDER_ATTRS = ["client_id", "active", "name", "parent_id", "cloud_key"]
ATTACH_ATTRS = ["name", "for_delete", "cloud_key", "clouds_folder_id", "sync_cloud_folder_id"]
MISSING_ERROR_MAX = 3

class clouds_snapshot(models.Model):
    """
    The model to keep history of changes per folders
    The model is introduced separately from clouds.folder to minimize risks of concurrent update:
     * While queue is prepared - a clouds.snapshot is used 
     * while queue is run - a clouds.folder is used

    The previous state is kept both for Odoo and cloud client
    State represent a json-formatted dict for all important clouds.folder dict
    """
    _name = "clouds.snapshot"
    _description = "Cloud folder snapshot"

    @api.depends("folder_id.parent_id")
    def _compute_parent_id(self):
        """
        Compute method for parent_id
        """
        for snapshot in self:
            parent_id = False
            if snapshot.folder_id.parent_id:
                parent_id = self.env["clouds.snapshot"].search(
                    [("folder_id", "=", snapshot.folder_id.parent_id.id)], limit=1
                )
            snapshot.parent_id = parent_id

    folder_id = fields.Many2one(
        "clouds.folder",
        "Folder",
        ondelete="cascade",
        index=True,
    )
    snapshot = fields.Text("Snapshot", default="{}")
    back_snapshot = fields.Text("Cloud Snapshot", default="{}")
    last_sync_datetime = fields.Datetime(
        "Queue Time", 
        default=lambda self: fields.Datetime.now(),
        index=True,
    )
    parent_id = fields.Many2one(
        "clouds.snapshot",
        compute=_compute_parent_id,
        compute_sudo=True,
        store=True,
    )
    task_ids = fields.One2many(
        "clouds.queue",
        "snapshot_id",
        string="Tasks",
    )
    reverse_state = fields.Selection(
        [
            ("normal", "Normal"),
            ("rearranged", "Reversed"),
            ("await", "Await Reversed"),
        ],
        default="normal",
        string="Reverse State",
        index=True,
    )
    move_state = fields.Selection(
        [
            ("normal", "Normal"),
            ("special_blocking", "Sync blocked"),
        ],
        default="normal",
        string="Move State",
        index=True,
        help="Special blocking if attachment is moved",
    )
    reverse_client_id = fields.Many2one("clouds.client", string="Previous Client")

    _order = "last_sync_datetime"

    def _prepare_folder_queue(self):
        """
        The method to find changes in Odoo and cloud client and create synced items
        This is the *core* method for sync algorithms 

        Methods:
         * _get_current_odoos_state
         * _get_current_client_state
         * create_task of clouds.queue
         * _relates_to_task_attachment of clouds.queue
         * _mark_obsolete of clouds.queue
         * _block_snapshot_for_move

        Returns:
         * dict of values to write in snapshot. The idea is to write simultaneously all vals and avoid concurrent
           updates

        Extra info:
         * Here we can adapt a queue safely, since we run in the same cron method. So, there should be no concurrent
           updates
         * Tasks with sequence lesser than 100 are blocking for child snapshopts
         * Expected singleton (but no ensure_one for performance issues) 
        """
        # We write each time to synced datetime before all checks in order NOT synced items are not ALWAYS come first
        # dummy_field is introduced to avoid merging writtening of snapshots in a single write, since last_sync_datetime
        # might be the same for a few (miliseconds are not take into account)
        snap_vals = {"last_sync_datetime":  fields.Datetime.now()}
        if self.reverse_state == "rearranged" or self.move_state == "special_blocking":
            return snap_vals

        # Get dict of previous and current folder values
        pre_state = json.loads(self.snapshot)
        new_state = self._get_current_odoos_state(self.folder_id) 
        pre_client_id = pre_state.get("client_id")
        new_client_id = new_state.get("client_id")
        act_client_id = pre_client_id or new_client_id
        if not act_client_id:
            return snap_vals
        
        checked_client = self.env["clouds.client"].browse(act_client_id).exists()
        if not checked_client or checked_client.state != "confirmed" or checked_client.error_state:
            # we check only active client which assumes receiving children. Others would be blocked in running queue
            return snap_vals

        #  If error - stops further processing. If 404 - a few attempts and consider as empty children
        #  We retrieve changes from active client: either previous or a new one
        new_back_state = self._get_current_client_state(act_client_id) 
        if new_back_state is None:
            return snap_vals

        # We write normal reverse_state for the cases of awaited children (if not going to be re-arranged)
        # We do that after checking for 404 to make sure such folders are not 'hanging' during reverse 
        # We save snapshots each time since in case of initial setup we anyway do not consider previous state
        pre_back_state = json.loads(self.back_snapshot)
        snap_vals.update({
            "reverse_state": "normal",
            "back_snapshot": json.dumps(new_back_state or {}), 
            "snapshot": json.dumps(new_state)}
        )
        new_attachment_ids = new_state.get("attachment_ids", []) 
        new_back_attachments_list = new_back_state and new_back_state.get("attachment_ids", []) or []

        # Consider changes happened in Odoo. No 'None'/'False' difference, since None > False is also a change
        folder_changes = []
        for folder_attr in FOLDER_ATTRS:
            if pre_state.get(folder_attr) != new_state.get(folder_attr):
                folder_changes.append(folder_attr)

        def _prepare_direct_sync_queue_folders():
            """
            The method to reflect own folder updates
            Parent and name are considered together, since for all clients it has the same API request
            """
            if "parent_id" in folder_changes or "name" in folder_changes:
                self.env["clouds.queue"]._create_task({
                    "name": "update_folder",
                    "task_type": "direct",
                    "client_id": act_client_id,
                    "folder_id": self.folder_id.id,
                    "args": json.dumps({"parent_key": new_state.get("parent_id")}),
                    "snapshot_id": self.id,
                    "sequence": 100, # not blocking, but important
                }) 

        def _prepare_direct_sync_queue_attachments():
            """
            The method to prepare tasks for changes detected in a Odoo

            Extra info:
             * we do not check for items in clouds, since previous tasks migth have been not yet proceeded
            """           
            def _get_sync_folder_id(ch_attach_dict):
                """
                The method to retrive folder which used for sync if an attachment was previously synced
                It might differ from snapshot folder, since attachment:
                 * might be moved between folders (might also include client change)
                
                Args:
                 * dict of read() ir.attachment

                Returns:
                 * clouds.folder object
                """
                sync_cloud_folder_id = self.folder_id
                if ch_attach_dict.get("sync_cloud_folder_id"):
                    synce_atta_folder_id = self.env["clouds.folder"].browse(
                        ch_attach_dict.get("sync_cloud_folder_id")
                    ).exists()
                    if synce_atta_folder_id:
                        sync_cloud_folder_id = synce_atta_folder_id
                return sync_cloud_folder_id

            def _archive_obsolete_tasks(ch_attachment_id, ch_folder_id):
                """
                The method to get by folders and archive attachment-related tasks which become senseless
                
                Args:
                 * ch_attachment_id ir.attachment object
                 * ch_folder_id - clouds.folder object
                """
                obsolete_task_ids = self.env["clouds.queue"]
                for task in ch_folder_id.task_ids:
                    if task._relates_to_task_attachment(ch_attachment_id, ch_attachment_id.cloud_key):
                        obsolete_task_ids += task 
                obsolete_task_ids._mark_obsolete()

            pre_attachment_ids = pre_state.get("attachment_ids", [])
            # iterate over changes detected to new attachments
            for new_attach_dict in new_attachment_ids:
                new_attach_id = new_attach_dict.get("id")
                pre_attach_dict_list = [
                    pre_attach for pre_attach in pre_attachment_ids if pre_attach.get("id") == new_attach_id
                ]
                if pre_attach_dict_list:
                    pre_attach_dict = pre_attach_dict_list[0]
                    if new_attach_dict.get("for_delete"):
                        # If recently marked for delete in Odoo > * DELETE IN CLOUDS *
                        if not pre_attach_dict.get("for_delete"): 
                            self.env["clouds.queue"]._create_task({
                                "name": "delete_file",
                                "task_type": "direct",
                                "client_id": act_client_id,
                                "folder_id": self.folder_id.id, 
                                "attachment_id": new_attach_id,
                                "snapshot_id": self.id,
                                "sequence": 300,
                            }) 
                    elif new_attach_dict.get("name") != pre_attach_dict.get("name"):
                        # If attachment name is changed > * UPDATE IN CLOUDS *
                        sync_cloud_folder_id = _get_sync_folder_id(new_attach_dict)
                        self.env["clouds.queue"]._create_task({
                            "name": "update_file",
                            "task_type": "direct",
                            "client_id": sync_cloud_folder_id.client_id.id,
                            "folder_id": sync_cloud_folder_id.id,
                            "attachment_id": new_attach_id,
                            "snapshot_id": self.id,
                            "sequence": 200,
                        })                           
                elif not new_attach_dict.get("for_delete"):
                    # new attachment is detected (which has not been deleted in meanwhile)
                    # as previous folder we ALWAYS use attachment used synced folder, since its previous tasks
                    # are there (covers also the case f1 > f2 > f3 ...)
                    sync_cloud_folder_id = _get_sync_folder_id(new_attach_dict) 
                    if new_attach_dict.get("cloud_key"):
                        # previously synced attachment: * MOVE IN CLOUDS (UPDATE/BACK TO ODOO+UPLOAD) *
                        # IMPOERANT: re-arranged sync_cloud_folder_id is totally fine here  
                        # we do not compare self.folder_id vs sync_cloud_folder_id to cover the case f1 > f2 > f1
                        self.env["clouds.queue"]._create_task({
                            "name": "move_file",
                            "task_type": "direct",
                            "client_id": act_client_id,
                            "folder_id": self.folder_id.id,
                            "attachment_id": new_attach_id,
                            "args": json.dumps({"no_odoo_unlink": True}),
                            "snapshot_id": self.id,
                            "prev_folder_id": sync_cloud_folder_id.id,  # for optimizing blocking
                            # blocking is based on prev folder attachment, while the task should be done ASAP
                            # no recursive block f1 > f2 > f1: (a) queue would be optimized; (b) run checks that
                            "sequence": 2, 
                        })
                        self._block_snapshot_for_move(sync_cloud_folder_id)
                        # if folder is re-arranged, it would be marked so afterwards. It cannot be re-arranged before
                        snap_vals.update({"move_state": "special_blocking"})
                    else:
                        # not yet synced attachment > * UPLOAD TO CLOUDS *
                        if sync_cloud_folder_id and self.folder_id != sync_cloud_folder_id:
                            # in case of change: synced folder is different > archive previous tasks: uploading & so on
                            attachment_id = self.env["ir.attachment"].browse(new_attach_dict.get("id")).exists()
                            if attachment_id:
                                _archive_obsolete_tasks(attachment_id, sync_cloud_folder_id)
                        self.env["clouds.queue"]._create_task({
                            "name": "upload_file",
                            "task_type": "direct",
                            "client_id": act_client_id,
                            "folder_id": self.folder_id.id,
                            "attachment_id": new_attach_id,
                            "snapshot_id": self.id,
                            "sequence": 100,
                        })            
            # iterate over 'missed' items in previous attachments
            for pre_attach_dict in pre_attachment_ids:
                pre_attach_id = pre_attach_dict.get("id")
                new_attach_dict_list = [
                    new_attach for new_attach in new_attachment_ids if new_attach.get("id") == pre_attach_id
                ] 
                if not new_attach_dict_list:
                    # attachment was previously, but now it "somehwere" (different folder or without a folder)
                    # if new folder has client, the scenario would be processed in new_attachments. Otherwise, here
                    attachment_id = self.env["ir.attachment"].browse(pre_attach_dict.get("id")).exists()
                    if attachment_id:
                        sync_cloud_folder_id = _get_sync_folder_id(pre_attach_dict)
                        new_cl_folder_id = attachment_id.clouds_folder_id
                        if sync_cloud_folder_id and sync_cloud_folder_id != new_cl_folder_id:                       
                            if not new_cl_folder_id or not new_cl_folder_id.client_id \
                                    or new_cl_folder_id.snapshot_id.reverse_state == "rearranged":                               
                                # 'rearranged' check: (a) might become non-synced; (b) if there was a move detected
                                # previously, it would be just replaced with this one; (c) if previous detected move
                                # was done, this would be the same folder move with no consequences
                                if attachment_id.cloud_key:
                                    # an item was previously synced > * MOVE IN CLOUDS (BACK TO ODOO+NO UPLOAD) *
                                    self.env["clouds.queue"]._create_task({
                                        "name": "move_file",
                                        "task_type": "direct",
                                        # IMPORTANT: if not new client > use previous, since client is required
                                        "client_id": new_cl_folder_id.client_id and new_cl_folder_id.client_id.id \
                                                     or attachment_id.sync_client_id \
                                                     and attachment_id.sync_client_id.id or act_client_id, 
                                        "folder_id": new_cl_folder_id.id, 
                                        "attachment_id": pre_attach_id,
                                        "args": json.dumps({"no_odoo_unlink": True}),
                                        "snapshot_id": new_cl_folder_id and new_cl_folder_id.snapshot_id.id,
                                        "prev_folder_id": sync_cloud_folder_id.id, # for optimizing blocking
                                        # blocking is based on prev fol attachment, while the task should be done ASAP
                                        # no recursive block f1>f2>f1: (a) queue would be optimized; (b) run checks that
                                        "sequence": 2,
                                    })
                                    self._block_snapshot_for_move(new_cl_folder_id)
                                    self._block_snapshot_for_move(sync_cloud_folder_id)
                                else:
                                    # an item was not previously synced (fine for not synced fol) > archive related tasks
                                    _archive_obsolete_tasks(attachment_id, sync_cloud_folder_id)
                            else:
                                # new folder of an attachment is synced (has client) > await for new snapshot checks
                                # previous folder however is blocked to avoid further changes and hence speed up move
                                self._block_snapshot_for_move(sync_cloud_folder_id)                      

        def _prepare_back_sync_queue():
            """
            The method to prepare tasks for changes detected in a client        
             IMPORTANT: no check for existing Odoo attachment which is moved: it is assumed deletion > new attachment
             IMPORTANT: while preparing tasks for subfolders we assume that their child items would be processed 
                        during further tasks' preparation  
            """
            s_childs = new_state.get("child_ids", [])
            synced_folder_ids = set([fol.get("cloud_key") for fol in s_childs])
            new_back_folders_list = new_back_state.get("folder_ids", [])
            pre_back_attachments_list = pre_back_state.get("attachment_ids", [])
            pre_back_folder_list = pre_back_state.get("folder_ids", [])
            to_delete_attachment_list = pre_back_attachments_list.copy()
            # iterate over changes detected to new files
            for new_atta_dict in new_back_attachments_list:
                for back_atta_dict in pre_back_attachments_list:
                    if new_atta_dict.get("cloud_key") == back_atta_dict.get("cloud_key"):
                        # file name is changed > * ODOO RENAME *
                        if new_atta_dict.get("name") != back_atta_dict.get("name"):                          
                            self.env["clouds.queue"]._create_task({
                                "name": "change_attachment",
                                "task_type": "backward",
                                "client_id": act_client_id,
                                "folder_id": self.folder_id.id,
                                "cloud_key": new_atta_dict.get("cloud_key"),
                                "snapshot_id": self.id,
                                "sequence": 100,
                            }) 
                        if back_atta_dict in to_delete_attachment_list:
                            to_delete_attachment_list.remove(back_atta_dict)
                        break
                else:
                    # no cloud_key is found in previous cloud state attachments > check whether we should create
                    exist_in_odoo = [
                        atta for atta in new_attachment_ids if new_atta_dict.get("cloud_key") == atta.get("cloud_key")
                    ]
                    if not exist_in_odoo:
                        # new file appeared but not inside the same Odoo folder > * ODOO CREATE *
                        # check is done per current folder only: otherwise it would be deleted and re-created
                        self.env["clouds.queue"]._create_task({
                            "name": "create_attachment",
                            "task_type": "backward",
                            "client_id": act_client_id,
                            "folder_id": self.folder_id.id,
                            "cloud_key": new_atta_dict.get("cloud_key"),
                            "snapshot_id": self.id,
                            "sequence": 200,
                        }) 
            # iterate over 'missed' items
            for del_atta_dict in to_delete_attachment_list:
                exist_in_odoo = [
                    atta.get("id") for atta in new_attachment_ids 
                    if del_atta_dict.get("cloud_key") == atta.get("cloud_key")
                ]  
                if exist_in_odoo:
                    # no item in clouds > * ODOO DELETE *
                    self.env["clouds.queue"]._create_task({
                        "name": "unlink_attachment",
                        "task_type": "backward",
                        "client_id": act_client_id,
                        "folder_id": self.folder_id.id,
                        "cloud_key": del_atta_dict.get("cloud_key"),
                        "attachment_id": exist_in_odoo[0],
                        "snapshot_id": self.id,
                        "sequence": 300,
                    })                
            # iterate over changes detected to new folders
            for new_fol_dict in new_back_folders_list:
                for back_fol_dict in pre_back_folder_list:
                    if new_fol_dict.get("cloud_key") == back_fol_dict.get("cloud_key"): 
                        break
                else:
                    # no cloud_key is found in previous cloud state folders > check whether we should create
                    if new_fol_dict.get("cloud_key") not in synced_folder_ids:
                        # new folder appeared but not inside the same Odoo folder > * ODOO FOLDER CREATE *
                        self.env["clouds.queue"]._create_task({
                            "name": "create_subfolder",
                            "task_type": "backward",
                            "client_id": act_client_id,
                            "folder_id": self.folder_id.id,
                            "cloud_key": new_fol_dict.get("cloud_key"),
                            "snapshot_id": self.id,
                            "sequence": 100, # a little bit more important sice assumes further recursive update
                        })

        def _initial_setup():
            """
            The method to prepare tasks for the very first sync (no check for previous states)
            """
            self.env["clouds.queue"]._create_task({
                "name": "setup_sync",
                "task_type": "direct",
                "client_id": act_client_id,
                "folder_id": self.folder_id.id,
                "snapshot_id": self.id,
                "sequence": 1, # blocking the most important since critical for each attachment and childs
            })
            for new_attach_dict in new_attachment_ids:
                if new_attach_dict.get("cloud_key"):
                    sync_cloud_folder_id = new_attach_dict.get("sync_cloud_folder_id") \
                        and self.env["clouds.folder"].browse(new_attach_dict.get("sync_cloud_folder_id")).exists() \
                        or False
                    if sync_cloud_folder_id and sync_cloud_folder_id != self.folder_id:
                        # moved from another folder. 'lost' otherwise
                        self.env["clouds.queue"]._create_task({
                            "name": "move_file",
                            "task_type": "direct",
                            "client_id": act_client_id,
                            "folder_id": self.folder_id.id,
                            "attachment_id": new_attach_dict.get("id"),
                            "args": json.dumps({"no_odoo_unlink": True}),
                            "snapshot_id": self.id,
                            "prev_folder_id": sync_cloud_folder_id.id,  # for optimizing blocking
                            # blocking is based on prev folder attachment, while the task should be done ASAP
                            # no recursive block f1 > f2 > f1: (a) queue would be optimized; (b) run checks that
                            "sequence": 2, 
                        })
                        self._block_snapshot_for_move(sync_cloud_folder_id)
                        # if folder is re-arranged, it would be marked so afterwards. It cannot be re-arranged before
                        snap_vals.update({"move_state": "special_blocking"})
                else:
                    self.env["clouds.queue"]._create_task({
                        "name": "upload_file",
                        "task_type": "direct",
                        "client_id": act_client_id,
                        "folder_id": self.folder_id.id,
                        "attachment_id": new_attach_dict.get("id"),
                        "snapshot_id": self.id,
                        "sequence": 100, # not blocking, but more important than updates/deletion
                    })                

        def _reflect_changes():
            """
            Submethod to sync backward and direct changes

            Methods:
             * _prepare_direct_sync_queue_folders
             * _prepare_direct_sync_queue_attachments
             * _prepare_back_sync_queue
            """
            _prepare_direct_sync_queue_folders()  
            _prepare_direct_sync_queue_attachments() 
            if new_back_state is not False:
                # condition is needed for the case of reverse sync and deleted hierarchy
                # in normal sync we would never be in this method, since we would come to initial setup
                _prepare_back_sync_queue()

        def _reverse_sync(subfolder_vals):
            """
            Submethod to prepare tasks for retrieving all items from clouds to Odoo

            Args:
             * subfolder_vals - values to write in created subfolder to trigger it reverse sync as well

            Methods:
             * _reflect_changes
            """
            # finalize all sync tasks to make sure we are ready to make reverse sync
            _reflect_changes()
            # adapt tasks: we write all conditions explicitly to avoid any misunderstanding in the Future
            obsolete_task_ids =  self.env["clouds.queue"]
            for task in self.task_ids:
                if task.active:
                    if task.task_type == "reverse":
                        # such tasks should not be here since reversed tasks might exist only for rearranged folders
                        pass
                    elif task.task_type == "direct":
                        # direct tasks are senseless, since we anyway get back everything to Odoo
                        if task.name == "delete_file":
                            # however one exception is deletion since we need make 'unlink' 
                            task.write({
                                "name": "{}_reverse".format(task.name),
                                "sequence": 20, # blocking
                            })
                        elif task.name in ["move_file"]:
                            # attachments should be moved before reversing to Odoo
                            pass
                        else:
                            obsolete_task_ids += task
                    elif task.task_type == "backward":
                        if task.name in ["create_subfolder", "create_attachment"]:
                            # we should create Odoo attachments and subfolders if they are introduced in cloud client
                            task.write({
                                "name": "{}_reverse".format(task.name),
                                "sequence": task.name == "create_subfolder" and 3 or 30,
                                "args": json.dumps(subfolder_vals),
                            })
                        else:
                            # renaming and deletion is not assumed to be reflected
                            obsolete_task_ids += task
            else:
                obsolete_task_ids._mark_obsolete()

            for new_attach_dict in new_attachment_ids:
                # Items from back sync are not taken into account since they would be processed in related task
                # Mark for deleted attachments are not considered: we just fully unlink those in a special task
                # Surely, attachment should have cloud key to be reversed (not synced items should not be adapted)

                # IMPORTANT: if any item is moved to this folder, it would also wait for 'adapt_attachment_reverse'
                if not new_attach_dict.get("for_delete") and new_attach_dict.get("cloud_key"):
                    self.env["clouds.queue"]._create_task({
                        "name": "adapt_attachment_reverse",
                        "task_type": "reverse",
                        "client_id": act_client_id,
                        "folder_id": self.folder_id.id,
                        "attachment_id": new_attach_dict.get("id"),
                        "snapshot_id": self.id,
                        "sequence": 500, # the very last operation for all reversely synced attachments
                    })

            # save the state as a new but mark re-arranged to make sure all prepared tasks are run
            snap_vals.update({
                "reverse_state": "rearranged", 
                "reverse_client_id": act_client_id, 
                "back_snapshot": "{}", 
                "snapshot": "{}"
            })
            # mark child snapshots which also require revese sync as awaiting reverse => to block this
            # folder unlink untill children folder are also done
            # we make only 'normal' folders as awaiting since, no sense to mark already re-arranged or await
            child_snapshot_ids = self.env["clouds.snapshot"].search([
                ("reverse_state", "=", "normal"),
                ("id", "child_of", self.id),
                ("id", "!=", self.id),
            ])
            # concurency is assumed to be avoided since those sanpshots are not touched here + each iteration commit
            child_snapshot_ids.write({"reverse_state": "await"})         

        ################################################################################################################
        ############## DEFINE WHAT SHOULD BE DONE BASED ON CLIENT AND ACTIVE STATES ####################################
        ################################################################################################################
        if "client_id" in folder_changes:
            # folder has a new client_id
            if pre_client_id:
                # old client is removed > Get back everything from client to Odoo
                # it also covers the case when a client was deactivating (in resetting client is unlinked from folders)
                _reverse_sync({
                    "client_id": new_client_id, 
                    "active": new_state.get("active"),
                    "pre_client_id": pre_client_id,
                    "pre_active": pre_state.get("active"),
                })
                return snap_vals
            if new_client_id:
                # new client is fine > make initial setup. Get here in the loop when pre_client is already reversed        
                if new_state.get("active"):
                    # but folder for sure should be active
                    _initial_setup()
        elif "active" in folder_changes:
            # client has not been changed, but folder own 'active' is changed
            if new_state.get("active"):
                # folder is reactivated > Make initial setup
                _initial_setup()
            else:
                # folder is deactivated > Get back everything from client to Odoo
                _reverse_sync({"active": new_state.get("active"), "pre_active": pre_state.get("active"),})
                return snap_vals
        else:
            # no client-related or active-related changes were detected
            if new_client_id:
                if new_back_state is False:
                    # cloud client returns 404/204/missing error in a few attempts --> re-create everything
                    _initial_setup()
                else:
                    # new client is fine > sync to a new client changes only 
                    _reflect_changes()
            else:
                # folder has inactive client > nothing to do. Leaf is shown for transperancy reasons
                pass
        return snap_vals

    @api.model
    def _get_current_odoos_state(self, folder_id):
        """
        The method to read the current state of Odoo objects
        
        Args:
         * folder_id - clouds.folder object

        Methods:
         * _filter_non_synced_attachments of ir.attachment

        Returns: 
         * dict of values:
          * id - int
          * active - bool
          * name - char
          * parent_id - int
          * client_id - int
          * attachment_ids - list of dicts
            ** id - int
            ** name - char
            ** for_delete - boolean

        Extra info:
         * IMPORTANT: binary content is not assumed to be changed in Odoo after a sync (since it is of URL type)
         * we are with the decorator api@model and the arg folder_id to be able to trigger the method in folder create   
        """
        folder_id = folder_id.with_context(active_test=False)
        folder_vals = folder_id.read(FOLDER_ATTRS, load=False)[0]
        attachment_vals_list = []
        child_folder_vals_list = []
        if folder_id.attachment_ids:
            s_attachment_ids = folder_id.attachment_ids._filter_non_synced_attachments()
            attachment_vals_list = s_attachment_ids.read(ATTACH_ATTRS, load=False)
        if folder_id.child_ids:
            child_folder_vals_list = folder_id.child_ids.read(FOLDER_ATTRS, load=False)
        folder_vals.update({
            "attachment_ids": attachment_vals_list,
            "child_ids": child_folder_vals_list,
        })
        return folder_vals

    def _get_current_client_state(self, client_id):
        """
        The method to read the current state of child items in cloud client
        
        Args:
         * client_id - int - id of clouds.client object

        Methods:
         * _api_get_child_items of clouds.client

        Returns:
         * dict of 
          ** folder_ids - dict - of cloud values (cloud_key, name, folder_type) - client files
          ** attachment_ids - dict - of cloud values (cloud_key, name, folder_type) - client subfolders
         * None if the error
         * False if missing error (and hence re-tries) 

        Extra info:
         * we keep missing error in folders to avoid concurrent updates while working with snapshots.
        """
        self.ensure_one()
        child_elements = {"folder_ids": [], "attachment_ids": []}
        if self.folder_id.cloud_key:
            client_id = self.env["clouds.client"].browse(client_id)
            child_elements = client_id._api_get_child_items(self.folder_id.cloud_key)
            if child_elements is None:
                return None
            elif child_elements is False:
                if self.folder_id.missing_error_retry <= MISSING_ERROR_MAX:
                    self.folder_id.missing_error_retry = self.folder_id.missing_error_retry + 1
                    return None
                else:
                    # exceeds the max number of 404 error
                    existing_task_ids = self.env["clouds.queue"].search([
                        ("active", "=", True), ("folder_id", "=", self.folder_id.id)
                    ])
                    existing_task_ids.unlink()
                    self.folder_id.write({
                        "cloud_key": False, # to avoid child items to be synced unless this folder is synced
                        "missing_error_retry": 0,
                    })
                    return False
            else:
                self.folder_id.missing_error_retry = 0
        return child_elements

    @api.model
    def _extend_based_on_direct_sync(self, folder_id, attachment_id, action="create"):
        """
        The method to change odoo previous state based on the results of backward sync

        Args:
         * folder_id - clouds.folder object
         * attachment_id - ir.attachment object
         * action - char - either create, update, or delete
        """
        snapshot_id = folder_id.snapshot_id
        prev_snapshot = json.loads(snapshot_id.back_snapshot)
        attachment_vals_list = prev_snapshot.get("attachment_ids") or []
        if action == "create":
            attachment_vals_list.append({"cloud_key": attachment_id.cloud_key, "name": attachment_id.name})
        elif action == "write":
            existing_attachment = [attach_dict for attach_dict in attachment_vals_list 
                                   if attach_dict.get("cloud_key") == attachment_id.cloud_key]
            if existing_attachment:
                attach_index = attachment_vals_list.index(existing_attachment[0])
                attachment_vals_list[attach_index].update(
                    {"cloud_key": attachment_id.cloud_key, "name": attachment_id.name}
                )
        else:
            existing_attachment = [attach_dict for attach_dict in attachment_vals_list 
                                   if attach_dict.get("cloud_key") == attachment_id.cloud_key]
            if existing_attachment and existing_attachment[0] in attachment_vals_list:
                attachment_vals_list.remove(existing_attachment[0])

        prev_snapshot.update({"attachment_ids": attachment_vals_list})
        snapshot_id.write({"back_snapshot": json.dumps(prev_snapshot)})

    @api.model
    def _extend_based_on_back_sync(self, folder_id, attachment_id, action="create"):
        """
        The method to change odoo previous state based on the results of backward sync

        Args:
         * folder_id - clouds.folder object
         * attachment_id - ir.attachment object
         * action - char - either create, update, or delete
        """
        snapshot_id = folder_id.snapshot_id
        prev_snapshot = json.loads(snapshot_id.snapshot)
        attachment_vals_list = prev_snapshot.get("attachment_ids") or []
        if action == "create":
            attachment_vals_list.append(attachment_id.read(ATTACH_ATTRS, load=False)[0])
        elif action == "write":
            existing_attachment = [attach_dict for attach_dict in attachment_vals_list 
                                   if attach_dict.get("id") == attachment_id.id]
            if existing_attachment:
                attach_index = attachment_vals_list.index(existing_attachment[0])
                attachment_vals_list[attach_index].update(attachment_id.read(ATTACH_ATTRS, load=False)[0])
        else:
            existing_attachment = [attach_dict for attach_dict in attachment_vals_list 
                                   if attach_dict.get("id") == attachment_id.id]
            if existing_attachment and existing_attachment[0] in attachment_vals_list:
                attachment_vals_list.remove(existing_attachment[0])

        prev_snapshot.update({"attachment_ids": attachment_vals_list})
        snapshot_id.write({"snapshot": json.dumps(prev_snapshot)})

    @api.model
    def _extend_folders_on_back_sync(self, folder_id):
        """
        The method to change odoo previous state based on the results of backward sync

        Args:
         * folder_id - clouds.folder object
        """
        snapshot_id = folder_id.snapshot_id
        prev_snapshot = json.loads(snapshot_id.snapshot)
        folder_vals_list = prev_snapshot.get("folder_ids") or []
        folder_vals_list.append(folder_id.read(FOLDER_ATTRS, load=False)[0])
        prev_snapshot.update({"folder_ids": folder_vals_list})
        snapshot_id.write({"snapshot": json.dumps(prev_snapshot)})

    @api.model
    def _adapt_for_reverse_creation(self, folder_id, args):
        """
        The method to make sure that a subfolder created during reverse sync would trigger its own update

        Args:
         * folder_id - clouds.folder object
         * args - dict which might contain:
            client_id - new_client_id
            active - we active
            pre_client_id - previous client_id
            pre_active - previous active

        Extra info:
         * we explicitly write all previous and new values to make sure changes would be detected, since
           there migth be complex computes in meanwhile
        """
        folder_vals = {}
        if args.get("client_id") is not None:
            folder_vals.update({"client_id": args.get("client_id")})
        if args.get("active") is not None:
            folder_vals.update({"active": args.get("active")})
        folder_id.write(folder_vals)
        snapshot_id = folder_id.snapshot_id
        prev_snapshot = json.loads(snapshot_id.snapshot)
        snapshot_vals = {}
        if args.get("pre_client_id") is not None:
            snapshot_vals.update({"client_id": args.get("pre_client_id")})
        if args.get("pre_active") is not None:
            snapshot_vals.update({"active": args.get("pre_active")})
        prev_snapshot.update(snapshot_vals)
        snapshot_id.write({
            "snapshot": json.dumps(prev_snapshot),
            "reverse_state": "await",
        })
    
    @api.model
    def _block_snapshot_for_move(self, ch_folder_id):
        """
        The method to mark snapshot "special_blocking" to finalize attachment move

        Args:
         * folder_id - clouds.folder object

        Returns:
         * bool
        """
        if not ch_folder_id:
            return False
        ch_snapshot_id = ch_folder_id.snapshot_id
        if ch_snapshot_id.move_state == "normal":
            ch_snapshot_id.move_state = "special_blocking"

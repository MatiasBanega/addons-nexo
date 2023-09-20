# -*- coding: utf-8 -*-

import json
import time
from datetime import timedelta

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


CRON_TIMEOUT = 900 # Cron is assumed to last 15 min (900s; as odoo.sh timeout). Conf timeouts should be more or equal     
MAX_RETRIES = 8 # how many failures of running the task is possible
FOLDERS_TO_RPOCESS = 20 # how many folders to consider for preparing tasks in a single loop
TASKS_TO_TAKE = 40 # how many tasks to take in each loop processing


class clouds_queue(models.Model):
    """
    The model which represents an each sync task
    -- Principles --
     * We do not delete tasks but deactivate those for:
       ** to avoid continius clouds.queue unlink logger (impossible to remove without monkey patching)
       ** to provide better compute triggering, since depends on tasks_ids.active is better than just o2m table  
     * Sequence is used to block tasks with bigger sequence (not for ordering!)
       The idea is that tasks with higher sequence might be anyway processed if they are not blocked
       For example, task 1 (sequence 0) blocks task 2 (sequence 10), but task 3 (sequence 10) is not blocked.
       Thus, if the task 3 had lesser ID, it would be processed earlier than task 1.
       Sequence is also used to block child folder tasks: if there is any task with sequence lesser than 100, child tasks
       tasks cannot be processed.
    """
    _name = "clouds.queue"
    _description = "Sync Task"

    @api.depends("client_id.state", "client_id.error_state",
                 "folder_id.all_parent_task_ids.sequence", "folder_id.all_parent_task_ids.active",
                 "folder_id.task_ids.sequence", "folder_id.task_ids.active", "folder_id.task_ids.sequence_id",
                 "prev_folder_id.task_ids.active", "prev_folder_id.task_ids.sequence", 
                 "prev_folder_id.task_ids.attachment_id", "prev_folder_id.task_ids.attachment_id.cloud_key", 
                 "prev_folder_id.task_ids.cloud_key", "attachment_id.cloud_key",
    )
    def _compute_blocked(self):
        """
        Compute method for blocked:
         * block a task if its client is not any more confirmed / it has errors
         * block a task if its folder is blocked by parent tasks (parent tasks are blocking if their have sequence 
           lesser than 100)
         * block a task if its folder has tasks with lesser sequence (or the same sequence and id)
         * block if previouse folder has tasks related to this task attachment (disregarding sequence). This use
           case in introduced especially for moving tasks 

        Methods:
         * _relates_to_task_attachment

        Extra info:
         * check for 'active' in depends/filtering is excess since if deactivating we anyway clear all o2ms.
           However, for sudden scenarios it is better to leave it her 
         * no check for move_file in preceedings, since f1 > f2 > f1 scenarios is (a) optimized; (b) running
           would result in True, so its sequence 0 is totally fine 
        """
        for task in self:
            blocked = False
            if not task.client_id or task.client_id.state != "confirmed" or task.client_id.error_state:
                blocked = True
            if not blocked:
                if task.folder_id.all_parent_task_ids:
                    parents = task.folder_id.all_parent_task_ids.filtered(lambda ta: ta.active and ta.sequence < 100)
                    if parents:
                        blocked = True
            if not blocked:              
                preceedings = task.folder_id.task_ids.filtered(
                    lambda ta: ta.active and (ta.sequence < task.sequence or (ta.sequence == task.sequence
                        and ta.sequence_id < task.sequence_id))
                )
                if preceedings:
                    blocked = True
            if not blocked:
                prev_folder_id = task.prev_folder_id
                if prev_folder_id and prev_folder_id != task.folder_id and task.attachment_id:
                    for prev_task in prev_folder_id.task_ids:
                        if task._relates_to_task_attachment(task.attachment_id, task.attachment_id.cloud_key):
                            blocked = True
                            break
            task.blocked = blocked

    name = fields.Selection(
        [  
            ("setup_sync", "Create cloud folder"),
            ("update_folder", "Move/Rename cloud folder"),
            ("upload_file", "Upload cloud file"),
            ("update_file", "Update cloud file"),
            ("delete_file", "Delete cloud file"),
            ("move_file", "Move cloud file"),

            ("create_subfolder", "Create Odoo subfolder"),
            ("create_attachment", "Create Odoo attachment"), 
            ("change_attachment", "Update Odoo attachment"), 
            ("unlink_attachment", "Delete Odoo attachment"),
        
            ("create_subfolder_reverse", "Create Odoo subfolder (reverse)"),
            ("create_attachment_reverse", "Create Odoo attachment (reverse)"),   
            ("delete_file_reverse", "Remove deleted attachment (reverse)"),

            ("adapt_attachment_reverse", "Reverse attachment sync"),
            ("adapt_folder_reverse", "Reverse attachment sync"),             
        ],
        string="Task", 
        required=True,
        index=True, # becuase of _get_the_next_tasks
    )
    task_type = fields.Selection(
        [
            ("direct", "Direct"),
            ("backward", "Backward"),
            ("reverse", "Reverse"),
        ],
        string="Type",
        required=True,
        index=True, # becuase of _get_the_next_tasks
    )
    args = fields.Char(string="Arguments", default="{}")
    client_id = fields.Many2one(
        "clouds.client", 
        string="Clouds Client",
        ondelete="cascade",
    )
    snapshot_id = fields.Many2one(
        "clouds.snapshot",
        string="Snapshot",
    )
    folder_id = fields.Many2one(
        "clouds.folder",
        string="Folder",
        ondelete="cascade",
    )
    prev_folder_id = fields.Many2one(
        "clouds.folder",
        string="Previous Folder (for moves)",
        ondelete="cascade",
    )
    attachment_id = fields.Many2one(
        "ir.attachment", 
        string="Attachment",
        ondelete="cascade", 
    )
    cloud_key = fields.Char(string="Cloud Key")
    fail_num = fields.Integer("Failed attempts", default=0)
    next_attempt = fields.Datetime(
        string="Not eralier than", 
        default=lambda self: fields.Datetime.now(),
        index=True, # becuase of _get_the_next_tasks
    )
    sequence = fields.Integer(
        string="Sequence", 
        default=100,
        index=True, # becuase of _get_the_next_tasks
    )
    sequence_id = fields.Integer(
        string="ID Sequence",
        index=True,
    )
    blocked = fields.Boolean(
        string="Blocked",
        compute=_compute_blocked,
        compute_sudo=True,
        store=True,
        index=True, # becuase of _get_the_next_tasks
    )
    active = fields.Boolean(
        string="Active", 
        default=True,
        index=True,
    )

    _order = "blocked, id ASC"

    @api.model
    def action_prepare_and_run_queue(self):
        """
        The key sync method which assumes to run existing queue tasks and create new ones
        The key principle here is that we prefer firtly running run existing tasks, and only then prepare new ones
        We do that in a single cron methods to:
         1. Avoid concurrent updates
         2. Decrease period between cron jobs (less down time)
         3. Avoid blocking other crons (if there are not so many workers assigned)
         4. Increase sustainability of updates (only perception at the moment)

        Methods:
         * _caclulate_time_and_check_lock
         * _action_clouds_cleaner
         * _cloud_log of clouds.client
         * _return_client_context of clouds.client
         * _action_run_queue (twice)
         * _action_prepare_queue

        Extra info:
         * We trigger reverse sync done after preparing the queue to make sure we to make sure all possible snapshots
           are considered
         * we trigger the second run of queue after preparation to the case it is enough time left and to speed up
           sync in such a way
        """
        self = self.sudo()
        cron_timeout = self._caclulate_time_and_check_lock("cloud_base_lock_time")
        if not cron_timeout: # previous cron is not finished (or broken but we wait until its timeout)
            return
        self.env["clouds.client"]._cloud_log(True, "Cloud sync was started. Locked till: {}".format(cron_timeout))
        self = self.with_context(self.env["clouds.client"]._return_client_context())        
        self._action_clouds_cleaner()
        self._action_run_queue(cron_timeout)
        self._action_prepare_queue(cron_timeout)
        self._action_run_queue(cron_timeout)
        self.env["ir.config_parameter"].sudo().set_param("cloud_base_lock_time", "")
        self.env["clouds.client"]._cloud_log(True, "Cloud sync was finished. Unlocked")

    @api.model
    def _caclulate_time_and_check_lock(self, lock_parameter="cloud_base_lock_time"):
        """
        The method to:
         * define interval which is possible for running queue
         * guarantee that another cron job would not be runned for the time
        The idea behind locking is that each sync is assumed to be launched each 15 minutes. During this period
        no other sync operations should take place, unless this one is explicitly not finished
        
        Args:
         * lock_parameter - char - indicating which cron is locked (the method is also used for preparing folders
           queue)

        Returns: 
         * datetime.datetime
         * False if locked (another cron is either running or broken but we anyway wait until its 'timed out')

        Extra info:
         * cron timeout datetime is calculated as cron planned time, minus 100(1)seconds for guarantee the 'last' loop
        """
        Config = self.env["ir.config_parameter"].sudo()
        cron_timeout_time = fields.Datetime.now() + timedelta(0, CRON_TIMEOUT-1) #1sec to guarantee the next cron start
        prev_lock_datetime = Config.get_param(lock_parameter, "")
        if prev_lock_datetime:
            if fields.Datetime.from_string(prev_lock_datetime) <= fields.Datetime.now():
                Config.set_param(lock_parameter, cron_timeout_time)
            else:
                cron_name = lock_parameter == "cloud_base_lock_time" and "Cloud sync" or "Folders update"
                log_message = "{} was started but previous process has not yet finished. Locked till: {}".format(
                    cron_name, prev_lock_datetime
                )
                self.env["clouds.client"]._cloud_log(True, log_message, "WARNING")
                cron_timeout_time = False # sync should be stopped
        else:
            Config.set_param(lock_parameter, cron_timeout_time)
        self.env["sync.model"]._cloud_commit() # to make sure it is available immediately
        return cron_timeout_time and cron_timeout_time-timedelta(0, 100) or False 

    @api.model
    def _action_clouds_cleaner(self):
        """
        The method to:
         1. Delete previously deactivate tasks
         2. Unlink clients which are archived if there were no any more snapshots with with stated reverse_client_id
         3. Delete logs which are too old

        Methods:
         * _api_get_child_items of clouds.client

        IMPORTANT: this method is a part of the core cron method to avoid any possibility of concurrent updates
        Run it once a day approximately before the queue processing
        """
        Config = self.env['ir.config_parameter'].sudo()
        last_trigger = Config.get_param('cloud_base_cleaner_time', '')
        checked_time = fields.Datetime.now() - timedelta(days=1)
        last_trigger = last_trigger and fields.Datetime.from_string(last_trigger) or checked_time
        # if last_trigger <= checked_time:
        if 1 == 1:
            # 1
            deactivated_task_ids = self.search([("active", "=", False)])
            deactivated_task_ids.unlink()
            self.env["sync.model"]._cloud_commit()
            # 2
            archived_client_ids = self.env["clouds.client"].search([("active", "=",  False)])
            for client in archived_client_ids:
                root_children = client._api_get_child_items(client.root_folder_key)
                if not root_children:
                    # there was constant api error (including missing) > delete when exceeds max attempts
                    if client.archive_error_retry > 4:
                        client.unlink()
                    else:
                        client.archive_error_retry = client.archive_error_retry + 1
                elif not root_children.get("folder_ids"):
                    # no cloud directories any more
                    client.unlink()
                else:
                    # we should check the case, since the root folder might have non-synced manually created dirs
                    for cloud_folder in root_children.get("folder_ids"):
                        cloud_key = cloud_folder.get("cloud_key")
                        existing = self.env["clouds.folder"].search([("cloud_key", "=", cloud_key)], limit=1)                    
                        if existing:
                            break
                    else:
                        # no cloud directories which have peered Odoo folders > we may unlink                        
                        client.unlink()
                self.env["sync.model"]._cloud_commit()
            # 3
            cloud_log_days = int(Config.get_param('cloud_base.cloud_log_days', '3'))
            cloud_log_days = cloud_log_days >=3 and cloud_log_days or 3
            obsolete_day = fields.Date.today() - timedelta(days=cloud_log_days)
            obsolete_logs = self.env["clouds.log"].search([("log_date", "<", obsolete_day)])
            obsolete_logs.unlink()
            self.env["sync.model"]._cloud_commit()
            Config.set_param('cloud_base_cleaner_time', fields.Datetime.now())
       
    @api.model
    def _action_prepare_queue(self, cron_timeout):
        """
        The method to prepare/update queue of tasks based on changes in folders
        IMPORTANT NOTE: we are commiting in each loop iteration to:
          * avoid concurrent update which is result of Odoo ORM SQL query merging (since sync datetime is the same for
            a few snapshots)
          * not to care to extra writes inside preparation. For example, child snapshots might be both inside  
            currently checked snapshot_ids and be written inside preparation. So, it would be also the same
            object write
        
        Args:
         * cron_timeout - datetime after which cron should be stopped

        Methods:
         * _cloud_log of clouds.client
         * _return_client_context of clouds.client (required to get backward changes)
         * _get_next_snapshots
         * _prepare_folder_queue of clouds.snapshot
        """
        self.env["clouds.client"]._cloud_log(True, "Start preparing queue")
        processed_ids = []
        snapshot_ids = self._get_next_snapshots(processed_ids)
        while snapshot_ids and fields.Datetime.now() < cron_timeout:
            for snapshot in snapshot_ids:
                snap_vals = snapshot._prepare_folder_queue()
                snapshot.write(snap_vals)      
                self.env["clouds.client"]._cloud_log(
                    True, 
                    "The folder {},{} was checked for updates".format(snapshot.folder_id.name, snapshot.folder_id.id),
                    "DEBUG",
                )
                # IMPORTANT: do not relocate that. See the method description
                self.env["sync.model"]._cloud_commit()
            processed_ids += snapshot_ids.ids
            snapshot_ids = self._get_next_snapshots(processed_ids)
        self.env["clouds.client"]._cloud_log(True, "Stop preparing queue")      

    @api.model
    def _action_run_queue(self, cron_timeout):
        """
        The method to trigger parts of queue in a loop
        We are in loop to process queue by groups (not to select 5000 records)

        We assume that period for the cron is 15 minutes ==> 900 seconds (this is odoo.sh timeout)
        So, with a 60 seconds tolerance we should stop the queue at 840 seconds (60 seconds would be enough for a
        single task)
            
        Args:
         * cron_timeout - datetime after which cron should be stopped

        Methods:
         * _reapply_blockings
         * run_queue
        """
        self._reapply_blockings()
        self.env["clouds.client"]._cloud_log(True, "Start running queue")
        queue_response = 1
        while queue_response == 1:
            queue_response = self._run_queue(cron_timeout)
        self.env["clouds.client"]._cloud_log(True, "Stop running queue")

    @api.model
    def _get_next_snapshots(self, processed_ids=[]):
        """
        The method to return the next snapshots to check for changes

        Args:
         * processed_ids - list of ids which are already done in this job (unreasonalble to make eternal loop)

        Returns: 
         * clouds.snapshot recordset

        Extra info:
         * reverse_state 'rearranged' indicates that a snapshot is reversed, so we wait until all reverse tasks are done
        """
        return self.env["clouds.snapshot"].search(
            [   
                ("id", "not in", processed_ids), 
                ("reverse_state", "!=", "rearranged"),
                ("move_state", "=", "normal"),
            ], 
            limit=FOLDERS_TO_RPOCESS,
        ) 

    @api.model
    def _reapply_blockings(self):
        """
        The method:
         * to check whether re-arranged snapshots do not any more have active tasks > so reverse_state becomes normal 
         * to check whether all moves blocking that snapshots are done > so move_state becomes normal

        If so, make tasks to delete such folders from clouds and unlink the current sync
         1. Finalize move states. We start with that to 'ease' reverse_states
         2. Search only among very parented snapshots
            Sometimes their parent is not marked as re-arranged. In such a case, it would be added during the next
            preparation, but its children would be already planned in the tasks to be 'normal'. So, it is only
            needed to wait until those tasks are done
            This scenario however would happen only when child snaphosts are checked earlier than parent ones 
            and preparation cannot be finished within a single loop
         3. check that there are no moves from this folder
         4. check that child snapshots are normal

        Methods:
         * _create_task
         * _cloud_log of clouds.client
        """      
        self.env["clouds.client"]._cloud_log(True, "Start checking blocks")
        # 1
        move_snapshots = self.env["clouds.snapshot"].search([("move_state", "=", "special_blocking")])
        for move_snapshot in move_snapshots:
            folders = move_snapshot.folder_id + move_snapshot.folder_id
            tasks = folders.mapped("task_ids")
            for task in tasks:
                if task.active and task.name == "move_file":
                    break
            else:
                move_snapshot.move_state = "normal"
                self.env["sync.model"]._cloud_commit()

        # 2
        assume_done_snapshots = self.env["clouds.snapshot"].search([
            ("reverse_state", "=", "rearranged"),
            ("move_state", "=", "normal"), # 3
            ("task_ids", "=", False),
            "|",
                ("parent_id", "=", False),
                "&",
                    ("parent_id.reverse_state", "=", "normal"),
                    ("parent_id.move_state", "=", "normal"),
        ])
        for assumed in assume_done_snapshots:
            # 4
            not_done_child_snapshot_ids = self.env["clouds.snapshot"].search(
                [
                    ("id", "child_of", assumed.id),
                    ("id", "!=", assumed.id),
                    "|",
                        ("move_state", "!=", "normal"), # 3
                        "|", 
                            ("reverse_state", "=", "await"),
                            "&",
                                ("reverse_state", "=", "rearranged"), # state matters, since there might be normal folders
                                ("task_ids", "!=", False), 
                ], limit=1,
            )
            # sequence=0 ==> reverse sync blocks any further children tasks (e.g. newest folder)
            # it is safe since we checked that reverse sync tasks are not present in child folders
            if not not_done_child_snapshot_ids:
                self.env["clouds.queue"]._create_task({
                    "name": "adapt_folder_reverse",
                    "task_type": "reverse",
                    "client_id": assumed.reverse_client_id.id,
                    "folder_id": assumed.folder_id.id,
                    "sequence": 0,
                })       
                self.env["sync.model"]._cloud_commit()
        self.env["clouds.client"]._cloud_log(True, "Finish checking blocks")

    @api.model
    def _run_queue(self, cron_timeout):
        """
        The method to take and proceed a queue
        
        Args:
         * cron_timeout - datetime after which cron should be stopped

        Methods:
         * _get_the_next_tasks
         * _run_task
         * _process_fail

        Returns integer code:
         * 1 - if active tasks
         * 2 - no more active tasks (cron should be finished) 
         * 3 - timeouted (cron should be finished)

        Extra info:
         * need to commit each time anyway since timeouts migh be less than 15 minutes neglecting recommendations and 
           since might be some accidental stops. Otherwise, might be drastic scenarios when the same tasks would
           be run multiple times.
        """
        tasks = self._get_the_next_tasks()
        queue_response = tasks and 1 or 2
        for task in tasks:
            if fields.Datetime.now() >= cron_timeout:
                queue_response = 3
                break
            success = task._run_task()
            if success is None:
                success = task._process_fail(awaititing=True)
            if not success:
                success = task._process_fail()
            if success:
                task._delete_task()
            self.env["sync.model"]._cloud_commit()
        return queue_response

    @api.model
    def _get_the_next_tasks(self):
        """
        The method to get tasks to be run:
         * tasks should not be blcoked by parent / preceedings
         * tasks which are previously failed, should be taken with a delay
         * tasks should be active: archived tasks are not going to be run. They are planned for deletion
         * moves are prioritized sinc assume risk of moving between different clients, chained moves
         * reverse tasks are prioritized. It is also assumed that if reverse tasks exist, direct tasks cannot exist.
           So reverse tasks cannot be blocked by direct tasks 
         * tasks are ordered by ID - so by the moment of creation
        """
        basic_domain = [("next_attempt", "<=", fields.Datetime.now()), ("blocked", "=", False), ("active", "=", True)]
        reverse_domain = basic_domain + ["|", ("name", "=", "move_file"), ("task_type", "=", "reverse")]
        next_tasks = self.search(reverse_domain, limit=TASKS_TO_TAKE)
        if not next_tasks:
            next_tasks =  self.search(basic_domain, limit=TASKS_TO_TAKE)
        return next_tasks

    def _run_task(self):
        """
        The method to address task

        Returns:
         * Boolean - true if success

        Extra info:
         * we do not in try except here, since errors should be process in an api requests
        """
        client_method = "_{}".format(self.name)
        method_to_call = getattr(self.client_id, client_method)
        result = method_to_call(self.folder_id, self.attachment_id, self.cloud_key, json.loads(self.args))  
        return result

    def _delete_task(self):
        """
        The method to delete task after processing
        We write not only 'active' to make sure all o2m fields are correct        
        """ 
        self.write({"active": False, "client_id": False, "snapshot_id": False, "folder_id": False, 
                    "attachment_id": False})
        
    def _process_fail(self, awaititing=False):
        """
        The method to iterate over attempts
         1. Depending on number of failures we postpone expontially
            1 > 2^1*15 = 30minutes; 2 > 2^2*15 = 1h; 3> 2^3*15 = 2h; 4> 2^4*15 = 4h; 5> 2^5*15 = 8h
            6> 2^6 *15 = 16h; 7>2^7*15 = 32h, 8>2^8*15 = 64h, etc.
        
        Args:
         * awaititing - bool - not mark as failed but await of parent tasks (so not failure attempts should be detected)

        Methods:
         * _prepare_task_attrs

        Returns:
         * bool - true - if we exceeds the max number of failure attempts
        """
        result = False
        fail_num = self.fail_num
        if not awaititing:
            fail_num = self.fail_num + 1
        if fail_num >= MAX_RETRIES+1:
            log_message = "Sync task {} {} was fully canceled due to exceeding maximum re-tries number".format(
                self, self._prepare_task_attrs()
            )
            self.env["clouds.client"]._cloud_log(False, log_message, "DEBUG")
            result = True
        else:
            next_attempt = fields.Datetime.now() + timedelta(0, (2**fail_num)*15*60) #1 
            self.write({"fail_num": fail_num, "next_attempt": next_attempt}) 
        return result

    def _relates_to_task_attachment(self, attachment_id, cloud_key):
        """
        The method to define whether the task relates to the same attachment by id or by cloud_key

        Args:
         * attachment_id - ir.attachment object or False
         * cloud_key - str

        Returns:
         * bool

        Extra info:
         * we check both attachment cloud_key and own cloud_key   
         * Expected singleton 
        """
        result = False
        if self.active:
            this_cloud_key = attachment_id and attachment_id.cloud_key or False
            task_cloud_keys = (self.attachment_id and self.attachment_id.cloud_key or False, self.cloud_key)
            result = (attachment_id and self.attachment_id and attachment_id == self.attachment_id) \
                     or (cloud_key and cloud_key in task_cloud_keys) \
                     or (this_cloud_key and this_cloud_key in task_cloud_keys)
        return result

    @api.model
    def _optimize_folder_tasks(self, task_name, task_type, folder_id, attachment_id, cloud_key):
        """
        The method to archive tasks which become obsolete because of newly created task
        
        Args:
         * task_name - char
         * task_type - char
         * folder_id - clouds.folder object or False (!)
         * attachment_id - ir.attachment object
         * cloud_key - char

        Methods:
         * _relates_to_task_attachment

        Returns:
         * tuple
          ** bool - whether a task should be created
          ** clouds.queue recordset - tasks which become obsolete

        Extra info:
         * ?? no concurrent update is possible, since we do not write to tasks in preparing tasks (except reverse
           sync which does not assume creating considered here tasks)
         * we do not consider 'move_file' in tasks to otpimize, since it is always the last task and then snapshots
           are blocked
         * direct name update / move is always more important than backward attachment change. Even the former
           is really old, an the latter - contemporary 
        """
        obsolete_tasks = self.env["clouds.queue"]
        if task_type != "reverse":
            if task_name  == "update_file":
                for task in folder_id.task_ids:
                    if task._relates_to_task_attachment(attachment_id, cloud_key):
                        if task.name in ["upload_file", "delete_file", "unlink_attachment", "update_file", 
                                         "create_attachment"]:
                            # update is useless:
                            # * in case of not uploaded item / direct update: since it would use contempopary data
                            # * in case of deleted item: since no sense to make update
                            # (create_attachment is actually not possible since direct update cannot be triggered)
                            return False, obsolete_tasks
                        elif task.name in ["change_attachment"]:
                            # * direct change is more important than the backward sync
                            obsolete_tasks += task
            if task_name == "change_attachment":
                for task in folder_id.task_ids:
                    if task._relates_to_task_attachment(attachment_id, cloud_key):
                        if task.name in ["upload_file", "delete_file", "unlink_attachment", "update_file", 
                                         "change_attachment", "create_attachment"]:
                            # update is useless:
                            # * in case of uploaded item / direct update: since it would use contempopary data
                            # * in case of deleted item: since no sense to make update
                            # * in case of direct update: since direct change is more important
                            # (upload_file is actually not possible since direct update cannot be triggered)
                            return False, obsolete_tasks                           
            elif task_name ==  "delete_file":
                for task in folder_id.task_ids:
                    if task._relates_to_task_attachment(attachment_id, cloud_key):
                        if task.name in ["unlink_attachment", "delete_file"]:
                            # any previous unlink / delete is preferable
                            return False, obsolete_tasks
                        elif task.name in ["upload_file", "update_file", "change_attachment", "create_attachment"]:
                            # uploading and updating a file in useless, since it is already deleted
                            # (create_attachment is actually not possible, since cannot trigger direct delete)
                            obsolete_tasks += task            
            elif task_name == "unlink_attachment":
                for task in folder_id.task_ids:
                    if task._relates_to_task_attachment(attachment_id, cloud_key):
                        if task.name in ["unlink_attachment"]:
                            # any previous unlink is preferable
                            return False, obsolete_tasks
                        elif task.name in ["upload_file", "delete_file", "update_file", "change_attachment", 
                                           "create_attachment"]:
                            # updating a file in useless, since it is already deleted
                            # (upload_file is not possible, since not uploaded file cannot trigger backward unlink)
                            # backward unlink is preferable since does not assume API request
                            obsolete_tasks += task 
            elif task_name == "update_folder":
                for task in folder_id.task_ids:
                    if task.name in ["setup_sync", "update_folder"]:
                        # no sense to update folder if it has not been yet created or already planned to be updated
                        return False, obsolete_tasks
            elif task_name == "move_file":
                # CRITICAL: when previous merging exist for performance optimizing, this is crucial for correct moving
                # 1. all previous attachment moves should be unlinked, since as previous folder we have attachment
                #    sync folder. So, moves f1 > f2; f1 > f3, migth be safely combined only to f1 > f3                               
                # 2. we also archive all 'adapt_attachment_reverse' since they assume getting file back to a folder
                #    which is already incorrect. Simultaneously, new folder adapt_attachment_reverse, if needed,
                #    would be created after the move task
                # 3. we do not try to optimize a task based on 'delete_file'/unlink_attachment, since move_tasks
                #    would wait for such tasks; and while they are done, all this attachment-related tasks would 
                #    be unlinked. For extreme cases, however, we have checks 
                prior_move_task_ids = self.search([
                    ("attachment_id", "=", attachment_id.id),
                    ("name", "in", ["move_file", "adapt_attachment_reverse"]),
                    ("active", "=", True),
                ])
                obsolete_tasks += prior_move_task_ids
                if folder_id == attachment_id.sync_cloud_folder_id:
                    # series of moves lead us to the same folder > no need to make any further move
                    return False, obsolete_tasks
        return True, obsolete_tasks

    def _prepare_task_attrs(self):
        """
        The method to prepare task description for the logs
        
        Returns:
         * string

        Extra info:
         * Expected singleon (but for performance issues without self.ensure_one)
        """
        client_mes = "Folder: {},{}".format(self.folder_id.name, self.folder_id.id)
        if self.attachment_id:
            client_mes = "{}. Attachment: {},{}".format(client_mes, self.attachment_id.name, self.attachment_id.id)
        cloud_key = self.cloud_key or self.attachment_id and self.attachment_id.cloud_key
        if cloud_key:
            client_mes = "{}. Cloud Key: {}".format(client_mes, cloud_key) 
        return client_mes

    @api.model
    def _create_task(self, values):
        """
        The wrapper method for create to underake common actions such as optimizing/logging
        IMPORTANT: values.get("folder_id") migth be empty

        Methods:
         * _optimize_folder_tasks
         * _get_the_next_sequence_id
         * create
         * _prepare_task_attrs
         * _cloud_log of clouds.client
         * _mark_obsolete

        Returns:
         * clouds.queue object or False

        Extra info:
         * we are in try/except since it is better not to plan something rather then block sync for this snapshot
           almost forever
         * sequence_id is used to make the same name task consequentially. E.g. until an item has not changed its name,
           the second rename should not take place
           Even in case of merging there are a lot of tasks which would require such prioritization
        """
        folder_id = values.get("folder_id") and self.env["clouds.folder"].browse(values.get("folder_id")).exists() \
                    or self.env["clouds.folder"] 
        task = False
        try:
            need_create, obsolete_tasks = self._optimize_folder_tasks(
                task_name=values.get("name"),
                task_type=values.get("task_type"),
                folder_id=folder_id,
                attachment_id=values.get("attachment_id") \
                           and self.env["ir.attachment"].browse(values.get("attachment_id")).exists() or False,
                cloud_key=values.get("cloud_key"),
            )         
            if need_create:
                # for extreme cases when there 2 equal name tasks (_optimize_folder_tasks should make that impossible)
                sequence_int = max(folder_id.task_ids and folder_id.task_ids.mapped("sequence_id") or [0]) + 1
                values.update({"sequence_id": sequence_int})
                task = self.create(values)
                client_mes = "The task {},{} was planned: {}.".format(task.name, task.id, task._prepare_task_attrs())  
                task.client_id._cloud_log(True, client_mes, "DEBUG")
            obsolete_tasks._mark_obsolete()
        except Exception as er:
            task_cl = self.env["clouds.client"].browse(values.get("client_id"))
            task_cl._cloud_log(False, "The task {} was not planned. Reason: {}".format(values, er))
            return False
        return task

    def _mark_obsolete(self):
        """
        The method to archive tasks and log that
        """
        if self:
            self.write({"active": False})
            obsol_list = ["The task {},{}: ".format(ob.name, ob.id) + ob._prepare_task_attrs() for ob in self]
            obsol_mes = "; ".join(obsol_list)
            self.env["clouds.client"]._cloud_log(
                True, 
                "The tasks were archived since further tasks had made them obsolete: {}".format(obsol_mes),
                "DEBUG",
            )            

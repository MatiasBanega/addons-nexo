# -*- coding: utf-8 -*-

import itertools
import json
from collections import defaultdict
from sortedcontainers import SortedList

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tools.safe_eval import safe_eval


# attributes which migh triggering changes folder write(); "res_model", "res_id", , "documents_folder_id" are 
# not considered: they are used as search criteria to find a record to 'write'
UPDATED_FIELDS = ("source_name", "parent_id", "rule_id", "active",  "sequence")


class clouds_folder(models.Model):
    """
    The model which introduces a directory for Odoo attachments and other subdirectories

    -- Principles --
     * folder cannot be deleted, only deactivated. Rule-related folder cannot be modified at all
     * automatic (rule-related) folders can not have a parent as a manual folder. Automatic folders can have manual
       folders inside
     * child folder cannot have a different connector rather than its parent (recursive)
     * folder cannot have a different connector rather than its rule
    """
    _name = "clouds.folder"
    _description = "Folder"

    @api.depends("rule_id.client_id", "parent_id.client_id", "own_client_id")
    def _compute_client_id(self):
        """
        Compute method for client_id
        The ideas behind:
         (a) rule client is more important than own; if a rule does not have a client, folder should not also have it 
         (b) parent client is more importat than own client
        The method is hierarcically recursive
        IMPORTANT: it is critical to order self hierarhicly to calculate firtsly the parents and only then - children 
                   order of folders is *NOT* regulated by parent 

        Extra info:
         * actually the order of parent_client_id & rule_client id is not important, since rules have the same
           recursion logic, whilerule-related folders cannot be children to not rule-related ones. 
           However, for emergent cases it is preferable to apply the parent rule first, since it migth be also
           rule-related
         * manual folders within rule-related folders however might be moved to another parent and might be changed,
           so, in case parent folder does not have a client, it might be synced to any
         * clear_caches does not fully guarantee recursive update so we apply inverse on own_client_id and rule 
           client_id, which also serve for cleaning own_client_id when parent folder is cleared
         * have also a look at _compute_client_id of sync.model  
         * we do not 'check' rights in unlink since that is forbidden on csv level. Simultaneously, we have that
           in 'check' as 'write' since we should also check attachment rights
        """
        self.clear_caches() # to avoid taking parent-related cache and sudden error
        left_folder_ids = self
        while left_folder_ids:
            root_folder_ids = left_folder_ids.filtered(lambda fo: fo.parent_id not in left_folder_ids)
            for folder in root_folder_ids:
                folder.parent_client_id = folder.parent_id and folder.parent_id.client_id or False
                folder.rule_client_id = folder.rule_id and folder.rule_id.client_id or False
                client_id =  folder.parent_client_id or folder.rule_client_id  or False
                if not client_id and not folder.rule_id:
                    client_id = folder.own_client_id
                folder.client_id = client_id
            left_folder_ids -= root_folder_ids 

    @api.depends("parent_id.all_parent_task_ids.active", "parent_id.task_ids.active")
    def _compute_all_parent_task_ids(self):
        """
        Compute method for all_parent_task_ids
        Calculate in recursion all tasks by all parents
        As in case of compute_client_id we do our best to make sure folders are in correct order by parent
        """
        self.clear_caches() # to avoid taking parent-related cache and sudden error
        left_folder_ids = self
        while left_folder_ids:
            root_folder_ids = left_folder_ids.filtered(lambda fo: fo.parent_id not in left_folder_ids)
            for folder in root_folder_ids:
                all_task_ids = []
                if folder.parent_id:
                    all_task_ids = (folder.parent_id.all_parent_task_ids + folder.parent_id.task_ids).ids
                folder.all_parent_task_ids = [(6, 0, all_task_ids)]
            left_folder_ids -= root_folder_ids 

    @api.depends("client_id.icon_class")
    def _compute_icon_class(self):
        """
        Compute method for icon_class
        """
        for folder in self:
            icon_class = "fa fa-folder"
            if folder.client_id and folder.client_id.icon_class:
                ending = folder.rule_id and ".png" or "_manual.png"
                icon_class = "{}{}".format(folder.client_id.icon_class, ending)
            elif not folder.rule_id:
                icon_class += " text-warning"
            folder.icon_class = icon_class

    @api.depends("res_model", "res_id", "parent_id.access_res_model", "parent_id.access_res_id")
    def _compute_access_res_model(self):
        """
        Compute method for access_res_model & access_res_id
        The idea is that manual subfolders do not have own res_model and res_id, while their access is defined
        based on the access to the parent folder
        Method is recursive, so if the parent doesn't have res_model, we should check its parent and so on
        As in case of compute_client_id we do our best to make sure folders are in correct order by parent
        """
        self.clear_caches() # to avoid taking parent-related cache and sudden error
        left_folder_ids = self
        while left_folder_ids:
            root_folder_ids = left_folder_ids.filtered(lambda fo: fo.parent_id not in left_folder_ids)
            for folder in root_folder_ids:
                access_res_model = access_res_id = False
                res_model = folder.res_model 
                if folder.res_model:
                    access_res_model = folder.res_model 
                    access_res_id = folder.res_id
                elif folder.parent_id:
                    access_res_model = folder.parent_id.access_res_model
                    access_res_id = folder.parent_id.access_res_id
                folder.access_res_model = access_res_model
                folder.access_res_id = access_res_id
            left_folder_ids -= root_folder_ids 

    @api.depends("access_user_ids", "access_group_ids.users", "parent_id.restricted_users")
    def _compute_restricted_users(self):
        """
        Compute method for restricted_users
        The idea of the field is to keep easily available list of users to whom folder is restricted
        AND to keep parent folder restrictions
        Limitations are cumulative: a user should access own folder and its parents
        As in case of compute_client_id we do our best to make sure folders are in correct order by parent
        """
        self.clear_caches() # to avoid taking parent-related cache and sudden error
        left_folder_ids = self
        while left_folder_ids:
            root_folder_ids = left_folder_ids.filtered(lambda fo: fo.parent_id not in left_folder_ids)
            for folder in root_folder_ids:
                restricted_users = "[]"
                if not folder.res_model:
                    if folder.parent_id and folder.parent_id.restricted_users \
                            and folder.parent_id.restricted_users != "[]":
                        restricted_users = folder.parent_id.restricted_users
                    all_user_ids = folder.access_user_ids or self.env["res.users"]
                    if folder.access_group_ids:
                        all_user_ids += folder.access_group_ids.mapped("users")
                    if all_user_ids:
                        if restricted_users and restricted_users != "[]":
                            restricted_users = str(list(set(safe_eval(restricted_users)) & set(all_user_ids.ids)))
                            if restricted_users == "[]":
                                raise ValidationError(
                                    _("If applied: nobody would be able to access the folder {},{}".format(
                                        folder.name, folder.id)
                                    )
                                ) 
                        else:
                            restricted_users = str(all_user_ids.ids)
                folder.restricted_users = restricted_users
            left_folder_ids -= root_folder_ids 

    @api.depends("snapshot_ids")
    def _compute_snapshot_id(self):
        """
        Compute method for snapshot_id
        """
        for folder in self:
            folder.snapshot_id = folder.snapshot_ids and folder.snapshot_ids[0] or False

    @api.constrains('parent_id')
    def _check_parent_id(self):
        """
        Constraint method to avoid recursions

        Extra info:
         * we check for context since while preparing folders, recursion is not possible and that slighly increases
           performance
        """
        if not self._context.get("prepare_queue_context") and not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive folders.'))

    def _inverse_name(self):
        """
        Inverse method for name
        The goal is to remove illegal characters and make unique per parent
        
        Methods:
         * _remove_illegal_characters of ir.attachment

        Extra info:
         * Uniqueness is guaranteed by folder ID. We do not add iterator, since:
           (a) it assumes looping
           (b) the next synces might result in changed order of folders, and iterator would be 'strangely changed'
        """
        start_cron = fields.Datetime.now()
        for folder in self:
            name_formal = self.env["ir.attachment"]._remove_illegal_characters(folder.name, str(folder.id))
            existing_id = self.sudo().search([
                ("parent_id", "=", folder.parent_id.id),
                ("name", "=", name_formal), 
                ("id", "!=", folder.id),
            ], limit=1) 
            if existing_id:
                name_formal = "{} ({})".format(name_formal, folder.id)
            if name_formal != folder.name:
                folder.name = name_formal

    def _inverse_own_client_id(self):
        """
        Inverse method for own_client_id
        The idea is to clear subfolder clients if its parent is cleared. Since the backward sync would write such 
        ownclient_id, it might happen that after clearing rule/parent client, many folders would be remained 'to sync'.
        A user would have to clear each item, what is totally unacceptable
        An unsolvable problem of that method relates to the point that compute for client id would be triggered many
        times

        Extra info:
         * see also inverse own_client_id of sync.model
        """
        for folder in self:
            if not folder.own_client_id:
                child_folder_ids = self.sudo().with_context(active_test=False).search(
                    [("id", "child_of", folder.id), ("id", "!=", folder.id)
                ])
                if child_folder_ids:
                    child_folder_ids.write({"own_client_id": False})

    name = fields.Char(
        string="Name", 
        inverse=_inverse_name,
        index=True, # because inverse would be launched during folders preparation
    )
    source_name = fields.Char("Source name")
    parent_id = fields.Many2one(
        "clouds.folder", 
        string="Parent folder",
        ondelete="cascade",
        index=True,
    )
    child_ids = fields.One2many(
        "clouds.folder", 
        "parent_id",
        string="Child folders",
    )
    attachment_ids = fields.One2many(
        "ir.attachment",
        "clouds_folder_id",
        string="Attachments",
    )
    own_client_id = fields.Many2one(
        "clouds.client", 
        string="Clouds Client", 
        domain=[("state", "=", "confirmed")],
        ondelete="set null",
        inverse=_inverse_own_client_id,
    )
    parent_client_id = fields.Many2one(
        "clouds.client", 
        string="Parent Cloud Client",
        compute=_compute_client_id,
        compute_sudo=True,
        store=True,
    )
    rule_client_id = fields.Many2one(
        "clouds.client", 
        string="Rule Cloud Client",
        compute=_compute_client_id,
        compute_sudo=True,
        store=True,
    )
    client_id = fields.Many2one(
        "clouds.client",
        string="Cloud Client",
        compute=_compute_client_id,
        compute_sudo=True,
        store=True,
        recursive=True,
    )
    task_ids = fields.One2many(
        "clouds.queue",
        "folder_id",
        string="Sync tasks",
    )
    all_parent_task_ids = fields.Many2many(
        "clouds.queue",
        "clouds_queue_clouds_folder_rel_table",
        "clouds_queue_id",
        "clouds_folder_id",
        string="All parent tasks",
        compute=_compute_all_parent_task_ids,
        compute_sudo=True,
        store=True,
        recursive=True,
    )
    rule_id = fields.Many2one(
        "sync.model", 
        string="Generated by the rule",
        index=True, # for preparing queue
    )
    sequence = fields.Integer(string="Sequence", default=0)
    active = fields.Boolean(
        string="Active", 
        default=True,
        index=True, # for preparing queue
    )
    recursively_deactivated = fields.Boolean(
        string="Recursively archived",
        help="Archived since of folder parents is archived",
    )
    description = fields.Text(string="Notes")
    icon_class = fields.Char(
        string="Icon", 
        compute=_compute_icon_class,
        store=True,
    )
    res_model = fields.Char(
        string="Resource model",
        copy=False,
        index=True, # for preparing queue
    )  
    res_id = fields.Many2oneReference(
        string="Resource ID", 
        model_field="res_model", 
        copy=False,
        index=True, # for preparing queue
        recursive=True,
    ) 
    access_res_model = fields.Char(
        string="Access Resource Model",
        compute=_compute_access_res_model,
        compute_sudo=True,
        store=True,
        recursive=True,
    )
    access_res_id = fields.Integer(
        string="Access Resource id",
        compute=_compute_access_res_model,
        compute_sudo=True,
        store=True,
        recursive=True,
    )    
    access_user_ids = fields.Many2many(
        "res.users",
        "res_users_clouds_folder_rel_table",
        "res_users_rel_id",
        "clouds_folder_rel_id",
        string="Limit access to users",
    )
    restricted_users = fields.Char(
        string="User limitations (tech)",
        compute=_compute_restricted_users,
        compute_sudo=True,
        store=True,
        recursive=True,
    )
    access_group_ids = fields.Many2many(
        "res.groups",
        "res_groups_clouds_folder_rel_table",
        "res_groups_rel_id",
        "clouds_folder_rel_id",
        string="Limit access to groups",
    )
    cloud_key = fields.Char(string="Cloud key", copy=False)
    url = fields.Char(string="URL", copy=False)
    snapshot_ids = fields.One2many("clouds.snapshot", "folder_id", "Snapshots")
    snapshot_id = fields.Many2one(
        "clouds.snapshot",
        "Snapshot",
        compute=_compute_snapshot_id,
        compute_sudo=True,
        store=True,
    )
    missing_error_retry = fields.Integer(string="Missing error attempts", default=0)

    _order = "rule_id, sequence, id"

    def check_access_rule(self, operation):
        """
        Re-write to make check() of ir.attachment to work with clouds.folder references
        """
        if self._context.get("ir_attachment_security"):
            self.check(operation)
        super(clouds_folder, self).check_access_rule(operation=operation)

    @api.model
    def check(self, mode, values=None):
        """
        Re-write to introduce logic based on linked object if exists
        
        --- Logic of res-model & res_id ---
        * rule-first-level folders (e.g. 'Tasks', 'Projects', super 'Docs') would have only res_model stated, but
          not res_id (it is zero)
        * object-related folders would have res_model and res_id taken from that objects (e.g. project_task, 1 or
          documents.folder, 2)
        * manual folders (without rule or object) would not have res_model & res_id. NOTE: Enterprise Documents 
          folders cannot be manual, since if created it automatically generates workspace

        --- Folder-related security ---
        * rule-related folders are not manageable.
        * if there are user groups or users, we firstly check whether they do not block restriction. NOTE: rule-related 
          folders cannot have this restiction. 
          To-do: clear such settings for the case of auto workspace creation
        * if a folder has res_model but not res_id > we check access for that model. It is enough to check access levels
          without rules
        * if a folder has res_model & res_id, we check an access for object found by that params
        * if a folder does not have res_model and res_id, we check an access to parent recursively  

        --- Attachments-related security ---
        All attachments related to folders would have res_model and res_id in the following way:
         * ones related to clouds.folder with res_model & res_id would have the same res_model & res_id, except
           attachments linked to document.document
         * ones related to document.document, would have this document res_model, res_id
         * ones related to clouds.folder without res_model or without res_id would have this clouds.folder id as res_id
           and 'clouds.folder' as res_model. IMPORTANT: it is not possible for attachments just to have res_model
           but res_id as 0, since such attachment would not be available for anybody. So, this case covers
           also the situation of rule-first-level folders ('Tasks' containing task-related folders; 
           super 'Docs' containting workspace-related folders)

        Args:
         * mode - char - which actionw e check: "read", "write", "create", "unlink"

        Main problems:
         * settings are applied not in real time. And we would have all the stuff only after 
         * in create we do not have a chance to retrieve all the stuff..

        Extra info:
         * this check was developped in a similar way ir.attachments are checked for security
        """
        if self.env.is_superuser():
            return True
        access_mode = "write" if mode in ("create", "unlink") else mode
        by_object_ids = defaultdict(set)
        if self:
            self.env["clouds.folder"].flush(["access_res_model", "access_res_id"]) 
            self._cr.execute(
                """SELECT access_res_model, access_res_id, rule_id, restricted_users 
                   FROM clouds_folder WHERE id IN %s""", [tuple(self.ids)]
            )
            for res_model, res_id, rule_id, restricted_users in self._cr.fetchall():            
                if restricted_users and restricted_users != "[]":
                    allowed_user_ids = safe_eval(restricted_users)
                    if self.env.user.id not in allowed_user_ids:
                        raise AccessError(_("Action is not permitted due to folder users or groups limitations"))
                # rule-related folders cannot be changed manually (do not relate to attachments checks)
                if rule_id and mode == "write" and not self._context.get("ir_attachment_security"):
                    raise AccessError(_("It is not allowed to update rule-related folders manually"))
                if res_model and res_id:
                    # otherwise neither this folder, nor parent have linked res_model: everybody can access those
                    by_object_ids[res_model].add(res_id)
        if values:
            if values.get("res_model") and values.get("res_id"):
                by_object_ids[values["res_model"]].add(values["res_id"])
            elif values.get("parent_id"):
                # if parent is changed, should check its rights as well (rule does not block subfolders)
                self._cr.execute(
                    "SELECT access_res_model, access_res_id FROM clouds_folder WHERE id = %s", [values.get("parent_id")]
                )
                for res_model, res_id in self._cr.fetchall():            
                    if res_model and res_id:
                        by_object_ids[res_model].add(res_id)
        for res_model, res_ids in by_object_ids.items():
            if res_model not in self.env:
                continue
            if res_model == "res.users" and len(res_ids) == 1 and self.env.uid == list(res_ids)[0]:
                continue
            self.env[res_model].check_access_rights(access_mode)
            res_ids = list(filter(lambda fo_id: fo_id, list(res_ids)))
            if res_ids:
                records = self.env[res_model].browse(res_ids).exists()
                records.check_access_rule(access_mode)

    def _read(self, fields):
        """
        Re-write to implement security check
        """
        self.check("read")
        return super(clouds_folder, self)._read(fields)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Re-write to automatically create snapshots

        Methods:
         * _get_current_odoo_state of clouds.snapshot
         * _attachments_change

        Extra info:
         * context parameter save_snapshot_state (bool) - if True, it indicates that a created folder has already
           a client sibling, and it should be taken into account to avoid re-creation
        """
        if not self.env.is_superuser():
            # use an exxcess is_superuser to make sure the method would not be run thousands tumes
            for val in vals_list:
                self.check("create", values=val)
        records = super(clouds_folder, self).create(vals_list)
        snapshots_vals_list = records.mapped(lambda rec: {
            "folder_id": rec.id,
            "snapshot": self._context.get("save_snapshot_state") \
                        and json.dumps(self.sudo().env["clouds.snapshot"]._get_current_odoos_state(rec)) \
                        or "{}"
        })
        snapshot_ids = self.sudo().env["clouds.snapshot"].create(snapshots_vals_list)
        return records

    def write(self, values):
        """
        Re-write to manage deactivation and reactivation.
        We cannot do that in inverse since 'active' is written even it the same
        
        Methods:
         * _manage_inverse_active
         * _attachments_change
        """
        self.check("write", values=values)
        result = super(clouds_folder, self).write(values)
        if values.get("active") is not None and not self._context.get("no_recursive_deactivation"):
            self._manage_inverse_active()
        return result

    def copy(self, default=None):
        """
        Re-write to implement security check
        """
        self.check("write")
        return super(clouds_folder, self).copy(default)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """
        Re-write to check access rights
        """
        check_rights_mode = self._context.get("write_mode") and "write" or "read"

        ids = super(clouds_folder, self)._search(
            args, offset=offset, limit=limit, order=order, count=False, access_rights_uid=access_rights_uid
        )
        if self.env.is_superuser():
            return len(ids) if count else ids
        if not ids:
            return 0 if count else []
        orig_ids = ids
        ids = set(ids)

        by_object_ids = defaultdict(lambda: defaultdict(set))
        self._cr.execute(
            """SELECT id, access_res_model, access_res_id, restricted_users 
               FROM clouds_folder WHERE id IN %s""", [tuple(ids)]
        )
        restricted_folders = []
        for row in self._cr.dictfetchall():
            if row["restricted_users"] and row["restricted_users"] != "[]":
                allowed_users = safe_eval(row["restricted_users"])
                if self.env.user.id not in allowed_users:
                    restricted_folders.append(row["id"])                       
            res_model = row["access_res_model"]
            res_id = row["access_res_id"]
            if res_model or res_id:
                # otherwise neither this folder, nor parent have linked res_model: everybody can access those 
                by_object_ids[res_model][res_id].add(row["id"])
        ids.difference_update(restricted_folders)
        for res_model, targets in by_object_ids.items():
            if res_model not in self.env:
                continue
            if not self.env[res_model].check_access_rights(check_rights_mode, False):
                ids.difference_update(itertools.chain(*targets.values()))
                continue
            target_ids = list(filter(lambda fo_id: fo_id, list(targets)))
            allowed = self.env[res_model].with_context(active_test=False).search([("id", "in", target_ids)])
            for res_id in set(target_ids).difference(allowed.ids):
                ids.difference_update(targets[res_id])

        result = [id for id in orig_ids if id in ids]
        if len(orig_ids) == limit and len(result) < self._context.get("need", limit):
            need = self._context.get("need", limit) - len(result)
            result.extend(self.with_context(need=need)._search(args, offset=offset + len(orig_ids),
                                       limit=limit, order=order, count=count,
                                       access_rights_uid=access_rights_uid)[:limit - len(result)])

        return len(result) if count else list(result)

    def name_get(self):
        """
        Overloading the method, to reflect parent's name recursively
        """
        result = []
        for node in self:
            name = u"{}{}".format(node.parent_id and node.parent_id.name_get()[0][1] + '/' or '', node.name)
            result.append((node.id, name))
        return result

    @api.model
    def action_js_return_nodes(self):
        """
        The method to recursively preare hirarchy of directories (for JS minaly)

        Methods:
         * _return_nodes_recursive

        Returns:
         * list of folders dict with keys:
           ** id
           ** text - folder_name
           ** icon
           ** children - array with the same keys

        Extra info:
         * we should not move by folders without parent, but should move by a parent without AVAILABLE for this user
           parent. So, to show 'Tasks', if 'Projects' are not available.
           That's why we have to run the method under sudo and then clear items
         * SortedList is critical for performance on large numbers (e.g. 100k items) for checking "id in list"
        """
        self = self.with_context(lang=self.env.user.lang)
        res = []
        all_nodes = self.search([])       
        if all_nodes:
            nodes = all_nodes.filtered(lambda fol: not fol.parent_id or fol.parent_id not in all_nodes) 
            all_ids = SortedList(all_nodes.ids)
            edit_ids = SortedList(self.with_context(write_mode=True).search([]).ids)
            for node in nodes:
                res += node._return_nodes_recursive(all_ids, edit_ids)
        return res

    @api.model
    def action_js_find_folders_by_res_params(self, res_model, res_id):
        """
        The method to search for ab object folder

        Args:
         * res_model - char - name of checked folder
         * res_id - int

        Methods:
         * _return_nodes_recursive

        Returns:
         * list of dicts (actually this list would always have a single element or no element): 
           see _return_nodes_recursive
           IMPORTANT: dict for the current folder would have form_root: True (required to manage contextual action)

        Extra info:
         * if folder_id exists, but it is not available for this user, we do not try to show available children
           as it is done in the full jstree. The reason is that if object own folder is not available, no sense
           to show attachment box at all
        """
        folder_id = self.search([("res_model", "=", res_model), ("res_id", "=", res_id)], limit=1,)
        res = False
        if folder_id:
            all_ids = SortedList(self.search([("id", "child_of", folder_id.id)]).ids)
            edit_ids = SortedList(self.with_context(write_mode=True).search([("id", "child_of", folder_id.id)]).ids)
            res = folder_id._return_nodes_recursive(all_ids, edit_ids)[0]
            custom_data = res.get("data")
            if custom_data is not None:
                custom_data.update({"form_root": True})
        return res and [res] or []

    @api.model
    def action_js_return_edit_form(self):
        """
        The method to return folder editing form
        """
        return self.sudo().env.ref('cloud_base.clouds_folder_view_form').id

    @api.model
    def action_js_create_node(self, data):
        """
        The method to update node name

        Methods:
         * action_js_format_folder_for_js_tree
         * _order_node_after_dnd

        Returns:
         * dict of keys for js tree (except 'children') or False if error (mainly access rights warning)
        """
        name = data.get("text")
        parent_id = data.get("parent")
        if parent_id == "#":
            parent_id = False
        else:
            parent_id = int(parent_id)
        new_node = self.create({"name": name, "parent_id": parent_id})
        new_node._order_node_after_dnd(parent_id=parent_id, position=False)
        return new_node.action_js_format_folder_for_js_tree()

    def action_js_update_node(self, data, position):
        """
        The method to update node name

        Args:
         * data - dict of node params
         * position - false (in case it is rename) or int (in case it is move)

        Methods:
         * action_js_format_folder_for_js_tree
         * _order_node_after_dnd
        
        Returns:
         * dict of keys for js tree (except 'children') or False if error (mainly access rights warning)

        Extra info:
         * Expected singleton
        """
        new_name = data.get("text")
        new_parent_id = data.get("parent")
        new_parent_id = new_parent_id != "#" and int(new_parent_id) or False
        if self.name != new_name:
            self.name = new_name
        if self.parent_id.id != new_parent_id:
            self.parent_id = new_parent_id
        if position is not False:
            self._order_node_after_dnd(parent_id=new_parent_id, position=position)
        return self.action_js_format_folder_for_js_tree() 

    def action_js_delete_node(self):
        """
        The method to deactivate a node
        It triggers recursive deactivation of children

        Returns:
         * always True

        Extra info:
         * Expected singleton 
        """
        self.active = False
        return True

    def action_js_format_folder_for_js_tree(self, all_nodes=None, edit_nodes=None):
        """
        The method to prepare dict for node

        Args:
         * all_nodes - list of ids of clouds.folder which are available for the current user 
         * edit_nodes - list of ids of clouds.folder which are available for the current user for update

        Returns:
        * dict
         ** text - char
         ** id - int
         ** icon - char
         ** data - dict:
           *** url - char 
           *** rule_related - boolean (whether created by auto rule)
           *** res_model - char
           *** res_id - char
           *** edit_rights - right to change folder

        Extra info:
         * edit_right relies upon edit_nodes, since if a user initially doesn't have edit rights, this user
           would not be able to update a node and get here. In critical case, check would be done on Python level
         * Expected singleton 
        """
        result = False
        cur_id = self.id
        if all_nodes is None or cur_id in all_nodes:
            custom_data = {
                "url": self.url, 
                "rule_related": self.rule_id and True or False,
                "res_model": self.res_model,
                "res_id": self.res_id,
                "edit_right": (edit_nodes is None or cur_id in edit_nodes) and True or False,
            }
            result = {"text": self.name, "id": cur_id, "icon": self.icon_class, "data": custom_data}
        return result

    def _check_needed_update(self, vals):
        """
        The method to check whether written values actually differ from current values
        The idea behind is that read() is much faster, then write(), whie actual changes are introduced not so 
        frequently
        So, for performance issues it is better to check whether and what should a record be updated

        IMPORTANT: read() is more efficinet than applying to record attributes (fol_id[key] or fol_id[key].id)

        Args:
         * vals - dict of assumed values to be written

        Returns:
         * dict of values to be written; might be empty if nothing changed

        Extra info:
         * source_name is used to read instead of name because of inverse_name
         * Expected singleton
        """
        ex_vals = self.read(fields=UPDATED_FIELDS, load=False)[0]
        ex_vals.update({"name": ex_vals.get("source_name")})
        del ex_vals["source_name"]
        new_vals = {}
        for key, val in vals.items():
            if ex_vals.get(key) is not None and val != ex_vals.get(key):
                new_vals.update({key: val})
        return new_vals

    @api.model
    def _reconcile_folder(self, vals, reconcilled_ids=[]):
        """
        The method to create or update folder based on rules of the type 'model'
        
        This method assumes processing 2 types of automatic folders:
            1. Model-related folder - so, cumulative directories for object-related folders.  
            2. Object-related folder - so, of an Odoo record
        E.g. Contacts > John > Tasks > Task1: 'Contacts' & 'Tasks' are rule-related; 'John' & 'Task1' are object-related

        1. Model-related folders:
            a. Do not have linked res_id and res_model
            b. Should/Might be changed only in case if they related to the same rule and the same parent
               Otherwise, a brand new directory should be created.
               E.g. Contacts > John > Tasks (id=1) > Task1 is incorrect to make Contacts > Mike > Tasks (id=1) > Task1
               Instead, it should be Contacts > Mike > Tasks (id=2) > Task1. In that example, Tasks (id=1) would be 
               still linked to John and would have the same items.
            c. Odoo model <> model-related folder has one2many relations. Each model might have a few linked directories
        2. Oject-related folders:
            a. Always have res_model and res_id, so it is linked to an Odoo document
            b. Should/Might be changed disregarding parent and rule
               E.g. Contacts > John > Tasks  > Task1(id=1) ==> Porjects > Task1(id=1)
               Files related to Task1 would be passed together with an object
            c. Odoo Object <> Object-related folder has a one2one2 relation. There might be not a few folders for the 
               same Odoo object. It is placed to the parent which order is the highest (recursively)

        In such a way, the relation object-related folder > model-related folder is always the kept (John > Tasks)
        The relation model-related folder > object-related  folder is not kept (Contacts > John)

        The very special case of folders is linked to Odoo Enterprise Documents. Such directories should not be taken
        into account here. It is managed in the add-on by the method _reconcile_folder_enterprise
        However, the very parent sync-model related folders for Enterprise directories are reconciled also there

        Args:
         * vals - dict of folder values
         * reconcilled_ids - list of folders we previously managed (so no need to write on that)
           (should be actually passed only to object-related folders)

        Methods:
         * _check_needed_update

        Returns:
         * tuple:
           ** clouds.folder object or emtpy object if not found
           ** dict - vals to be created or False, if no object should be created
           ** folder_write - bool - whether any change to a folder was done (so, need to update attachments)
          IMPORTANT: the idea behind such return is to make multi create for folders, see _prepare_folders_recursively
          of sync.model
        """
        folder_write = False
        create_vals = False
        existing_domain = [
            ("res_id", "=", vals.get("res_id")), ("res_model", "=", vals.get("res_model")), ("rule_id", "!=", False), 
            "|", ("active", "=", True), ("active", "=", False),
        ]
        object_related_folder = vals.get("res_id") and vals.get("res_model") and True or False
        if not object_related_folder:
            existing_domain += [("parent_id", "=", vals.get("parent_id")), ("rule_id", "=", vals.get("rule_id"))]
        
        folder_id = self.search(existing_domain, limit=1)
        if folder_id:
            if folder_id.id not in reconcilled_ids:
                new_vals = folder_id._check_needed_update(vals)
                if new_vals:
                    folder_write = True
                    new_vals.update({"source_name": vals.get("name")})
                    folder_id.write(new_vals)
        else:
            create_vals = vals.copy()
            create_vals.update({"source_name": vals.get("name")})
        return folder_id, create_vals, folder_write

    def _create_default_folders(self, default_folders):
        """
        The method to generate folders and attachments assumed by the rule
        This method might involve a significant number of folders, so we should optimize it as much as possible
        That's why where it is possible we implement multi create
        
        Args:
         * default_folders - list of dicts, including icon, id, text, children (list: recursion)
        """
        new_attachment_vals_list = self._create_default_folders_recursive(default_folders, [])
        if new_attachment_vals_list:
            self.env["ir.attachment"].create(new_attachment_vals_list)

    def _create_default_folders_recursive(self, default_folders, new_attachment_vals_list):
        """
        The method to get default folders/attachments from the rule and create those
        
        Args:
         * default_folders - list of dicts, including icon, id, text, children (list: recursion)
         * new_attachment_vals_list- list of dicts for brand new attachments
        
        Methods:
         * _create_default_folders_recursive (recursion)
        """
        for d_folder in default_folders:
            if d_folder.get("icon") == "fa fa-file-o":
                atta_id = int(d_folder.get("id"))
                attachment_id = self.sudo().env["ir.attachment"].browse(atta_id).exists()
                if attachment_id:
                    new_attachment_vals_template = attachment_id.with_context(active_test=False).copy_data({})[0]
                    new_attachment_vals_template.update({"raw": attachment_id.raw,})
                    for record in self:
                        new_attachment_vals = new_attachment_vals_template.copy()
                        new_attachment_vals.update({"clouds_folder_id": record.id})
                        new_attachment_vals_list.append(new_attachment_vals)
            else:
                subolder_vals_list = []
                subfolder_vals_template = {"name": d_folder.get("text")}
                for record in self:
                    subfolder_vals = subfolder_vals_template.copy()
                    subfolder_vals.update({"parent_id": record.id})
                    subolder_vals_list.append(subfolder_vals)
                subfolder_ids = self.create(subolder_vals_list)
                new_attachment_vals_list = subfolder_ids._create_default_folders_recursive(
                    d_folder.get("children"), new_attachment_vals_list
                )
        return new_attachment_vals_list

    def _return_nodes_recursive(self, all_nodes=[], edit_nodes=[]):
        """
        The method to go by all nodes recursively to prepare their list in js_tree format

        Methods:
         * action_js_format_folder_for_js_tree

        Args:
         * all_nodes - SortedList of ids of clouds.folder which are available for the current user
         * edit_nodes - - SortedList of ids of clouds.folder which are available for the current user for update
           Used to avoid checking rights for each node

        Returns:
         * list of dicts (see action_js_format_folder_for_js_tree)
        
        Extra info:
         * we are under sudo to make sure all children are returned, but we show only those to which the current
           user has an access
         * Expected singleton
        """
        self = self.sudo()
        res = self.action_js_format_folder_for_js_tree(all_nodes, edit_nodes) or {}
        child_res = []
        for child in self.child_ids: 
            child_values = child._return_nodes_recursive(all_nodes, edit_nodes)
            child_res += child_values
        if res:           
            res.update({"children": child_res})
            res = [res]
        else:
            res = child_res
        return res

    def _order_node_after_dnd(self, parent_id, position):
        """
        The method to normalize sequence when position of Node has been changed based on a new element position and
        its neighbours.
         1. In case of create we put element always to the end
         2. We try to update all previous elements sequences in case it become the same of a current one (sequence
            migth be negative)

        Args:
         * parent_id - int - id of node
         * position - int or false (needed to the case of create)

        Extra info:
         * Epected singleton
        """
        self = self.sudo() #since rule-related nodes are updatable only under super user
        the_same_children_domain = [("id", "!=", self.id)]
        if parent_id:
            the_same_children_domain.append(("parent_id.id", "=", parent_id))
        else:
            the_same_children_domain.append(("parent_id", "=", False))
        this_parent_nodes = self.search(the_same_children_domain)
        if position is False:
            position = len(this_parent_nodes)
        if this_parent_nodes:
            neigbour_after = len(this_parent_nodes) > position and this_parent_nodes[position] or False
            neigbour_before = position > 0 and this_parent_nodes[position-1] or False
            sequence = False
            if neigbour_after:
                sequence = neigbour_after.sequence - 1
                # 1
                while neigbour_before and neigbour_before.sequence == sequence:
                    neigbour_before.sequence = neigbour_before.sequence - 1
                    position -= 1
                    neigbour_before = position > 0 and this_parent_nodes[position-1] or False
            elif neigbour_before:
                sequence = neigbour_before.sequence + 1
            if sequence is not False:
                self.sequence = sequence

    def _manage_inverse_active(self):
        """
        The pseudo-inverse method for active pursuing the goal of deactivating the child folders

        Methods:
         * _get_parent_rule_folder

        Extra info:
         * we under sudo() to make sure all children are deactivated
        """
        folders = self.sudo()
        while folders:
            folder = folders[0]
            if folder.active:
                child_folder_ids = self.with_context(active_test=False).search([
                    ("id", "child_of", folder.id), 
                    ("id", "!=", folder.id),
                    ("active", "=", False),
                    ("recursively_deactivated", "=", True),
                ])
                for fol in child_folder_ids:
                    if fol._get_parent_rule_folder() == folder:
                        fol.with_context(no_recursive_deactivation=True).write({
                            "active": True,
                            "recursively_deactivated": False,
                        })
            else:
                child_folder_ids = self.search([
                    ("id", "child_of", folder.id), 
                    ("id", "!=", folder.id),
                    ("active", "!=", False),
                ])
                child_folder_ids.with_context(no_recursive_deactivation=True).write({
                    "active": False,
                    "recursively_deactivated": True,
                })
                folders -= child_folder_ids
            folders -= folder

    def _get_parent_rule_folder(self):
        """
        The method to define to which rule current folder relates to

        The idea is to make sure that child folder relates the same parent by rule
        Othewise, it relates to some child folder rule. Example:
        - Projects 
            -- Project 1
                --- Manual folder 1
                --- Contacts
                    ---- John Brown
                        ----- Manual Folder 2
                            ------ Manual synfolder 2.1
                    ---- Manual folder 3
        - Marketing Docs
            -- Manual folder 4
            -- Brand 1
                --- Manual folder 5

        ==> MF 1 rule parent is Project 1. So, reactivating Projects would not lead to MF reactivation
        ==> MF 2 rule parent is John Brown
        ==> MF 2.1 rule parent is also John Bown (its parent MF2 is not rule-related)
        ==> MF 3 rule parent is Contacts
        ==> MF4 & MF5 would not have rule-related parents since they Enterprise Documents folders always have rule

        Returns:
         * clouds.folder object or False

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        folder_id = False
        parent_id = self.parent_id
        rule_id = self.rule_id
        while parent_id and not rule_id:
            if parent_id.rule_id:
                folder_id = parent_id
                break
            parent_id = parent_id.parent_id
        return folder_id

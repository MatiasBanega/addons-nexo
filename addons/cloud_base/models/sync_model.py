# -*- coding: utf-8 -*-

import json

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

FORBIDDENMODELS = ["ir.module.module", "mail.activity.mixin", "mail.thread", "ir.attachment", "documents.document",
                   "documents.folder", "sync.model", "clouds.folder", "clouds.snapshot"]
OBJECTS_TO_PROCESS = 1000  # based on performance tests on default psql conf

class sync_model(models.Model):
    """
    The model to manage model (+domain) - cloud folder relation
    """
    _name = "sync.model"
    _description = "Folder Rule"

    @api.depends("period_ids", "period_ids.field_id", "period_ids.period_value",
                 "period_ids.period_type", "period_ids.inclusive_this")
    def _compute_period_title(self):
        """
        Compute method for period_title & period_domain

        Methods:
         * _return_period_domain_and_title
        """
        for sync_model in self:
            period_domain, period_title = sync_model._return_period_domain_and_title()
            sync_model.period_domain = period_domain
            sync_model.period_title = period_title

    @api.depends("own_client_id", "parent_id.client_id")
    def _compute_client_id(self):
        """
        Compute method for client_id
        The idea is that parent client is more importat than own client
        The method is hierarcically recursive
        IMPORTANT: it is critical to order self hierarhicly to calculate firtsly the parents and only then - children 
                   order of folders is *NOT* regulated by parent

        Extra info:
         * look also at clouds.folder _compute_client_id
        """
        self.clear_caches() # to avoid taking parent-related cache and sudden error
        left_rule_ids = self
        while left_rule_ids:
            root_rule_ids = left_rule_ids.filtered(lambda fo: fo.parent_id not in left_rule_ids)
            for sync_model in root_rule_ids:
                sync_model.parent_client_id = sync_model.parent_id and sync_model.parent_id.client_id or False
                sync_model.client_id = sync_model.parent_client_id or sync_model.own_client_id
            left_rule_ids -= root_rule_ids

    @api.constrains("parent_id", "rule_type", "parent_field")
    def _check_parent_id(self):
        """
        Constraint method to:
         * avoid recursions
         * to make sure folders are of the same types
         * to make sure parent field relates to a correct model
        """
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive rules.'))
        for sync_model in self:
            if sync_model.parent_id:
                if sync_model.rule_type != sync_model.parent_id.rule_type:
                    raise ValidationError(_('Error! Parent Rule should be of the same type'))
                if sync_model.parent_field:
                    fields_chain = sync_model.parent_field.split(".")
                    current_parent = sync_model.model
                    c_field_instance = False
                    for c_field in fields_chain:
                        c_field_instance = self.sudo().env["ir.model.fields"].search([
                            ("model", "=", current_parent),
                            ("name", "=", c_field)
                        ])
                    else:
                        if c_field_instance.relation != sync_model.parent_id.model:
                            raise ValidationError(_('Error! Parent rule model is not equal to parent field model'))

    def _inverse_own_client_id(self):
        """
        Inverse method for own_client_id

        Extra info:
         * see also inverse own_client_id of clouds.folder
        """
        for sync_model in self:
            if not sync_model.own_client_id:
                child_rule_ids = self.sudo().with_context(active_test=False).search(
                    [("id", "child_of", sync_model.id), ("id", "!=", sync_model.id)
                ])
                if child_rule_ids:
                    child_rule_ids.write({"own_client_id": False})         
                folder_ids = self.env["clouds.folder"].sudo().with_context(active_test=False).search(
                    [("rule_id", "=", sync_model.id)
                ])
                folder_ids.write({"own_client_id": False})

    def _inverse_active(self):
        """
        Inverse method for active
        
        Extra info:
         * we under sudo() to make sure all children are deactivated
        """
        if not self._context.get("no_recursive_deactivation"):
            sync_models = self.sudo()
            while sync_models:
                sync_model = sync_models[0]
                if not sync_model.active:
                    child_model_ids = self.search([("id", "child_of", sync_model.id), ("id", "!=", sync_model.id)])
                    child_model_ids.with_context(no_recursive_deactivation=True).write({"active": False})
                    sync_models -= child_model_ids
                sync_models -= sync_model

    @api.onchange("model_id")
    def _onchange_model_id(self):
        """
        Onchange method for model_id
        """
        for sync_model in self:
            if sync_model.model_id:
                sync_model.name = self.model_id.name
            sync_model.domain = "[]"
            sync_model.default_folders = "[]"
            sync_model.period_ids = False
            sync_model.parent_id = False
            sync_model.parent_field = False

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        """
        Onchange method for parent_id
        """
        for sync_model in self:
            sync_model.parent_field = False

    name = fields.Char(string="Folder name", required=True)
    own_client_id = fields.Many2one(
        "clouds.client", 
        string="Clouds Client", 
        domain=[("state", "=", "confirmed")],
        inverse=_inverse_own_client_id,
    )
    parent_client_id = fields.Many2one(
        "clouds.client", 
        string="Parent Cloud Client",
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
    parent_id = fields.Many2one(
        "sync.model", 
        string="Parent rule",
        domain=[('rule_type', '=', 'model')],
        help="""
            If defined, related object folders would be created inside a folder related to the parent rule.
            To that end it is needed to define a field based on which parent-child relation of Odoo records might
            be distinguished.
            For example, to achieve the structure 'Odoo > Contacts > Agrolait > Tasks > Task 1', you should define the 
            rule (A) for Odoo partners, and the rule (B) for Odoo tasks. The rule A should be a parent for the rule B, 
            as a linked  field use 'Partner'
        """,
    )
    parent_field = fields.Char(
        string="Parent model field",
        help="""
            The field used to define parent-child relation. For example, if project-related rule is a parent for
            task-related rule, then task-related rule should have 'Project' as a parent model field. In such a way,
            it is possible to achive the structure Odoo > Projects > Project 1 > Project 1 tasks > Task 1
        """
    )
    child_ids = fields.One2many(
        "sync.model",
        "parent_id",
        string="Child Rules",
    )
    rule_type = fields.Selection(
        [("model", "Model-Related Rule")],
        string="Rule type",
        default="model",
        required=True,
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model to sync",
        domain=[("model", "not in", FORBIDDENMODELS), ("transient", "=", False)],
        ondelete='cascade',
    )
    model = fields.Char(related="model_id.model", store=True)
    domain = fields.Text(string="Filtering", default="[]")
    period_ids = fields.One2many(
        "cloud.domain.period",
        "sync_model_id",
        string="Periods",
    )
    period_domain  = fields.Char(string="Domain by periods", compute=_compute_period_title)
    period_title = fields.Char(string="If today, the periods would be", compute=_compute_period_title,)
    default_folders = fields.Char(string="Default Folders", default="[]")
    name_expression = fields.Text("Name Expression")
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(
        string="Active", 
        default=True,
        inverse=_inverse_active,
    )

    _order = "sequence, id"

    def write(self, vals):
        """
        Override to forbid changing critical fields (altough excess based on XML restrictions)
        """
        if vals.get("rule_type"):
            raise ValidationError(_("That's forbidden to change rule type after creation. Create a new rule instead"))
        if vals.get("model_id"):
            raise ValidationError(_("That's forbidden to change rule model after creation. Create a new rule instead"))
        return super(sync_model, self).write(vals)

    @api.model
    def action_prepare_auto_folders(self):
        """
        The router method to start preparing folders 

        Methods: 
         * _caclulate_time_and_check_lock of clouds.queue
         * _prepare_folders
         * _prepare_document_folders (if available)

        Extra info:
         * we under sudo() to make sure all folders are parsed
        """
        self = self.with_context(prepare_queue_context=True).sudo()
        cron_timeout = self.env["clouds.queue"]._caclulate_time_and_check_lock("cloud_base_folders_lock_time")
        if not cron_timeout: # previous cron is not finished (or broken but we wait until its timeout)
            return

        Config = self.env['ir.config_parameter'].sudo()
        if hasattr(self, "_prepare_document_folders"):
            # the module 'cloud_base_documents' is installed > prepare the both rules in turn
            route_order = int(Config.get_param("cloud_base_rules_order", "1"))
            if route_order == 1:
                Config.set_param("cloud_base_rules_order", "2")
                not_timeouted = self._prepare_folders(cron_timeout)
                if not_timeouted:
                    self._prepare_document_folders(cron_timeout)
            else:
                Config.set_param("cloud_base_rules_order", "1")
                not_timeouted = self._prepare_document_folders(cron_timeout)
                if not_timeouted:
                    self._prepare_folders(cron_timeout)                
        else:
            self._prepare_folders(cron_timeout)
        Config.set_param("cloud_base_folders_lock_time", "")
    
    def _cloud_commit(self):
        """
        The method to make cr commit
        Introduced to be able to make tests without commiting
        """ 
        if not self._context.get("cloud_testing"):
            self._cr.commit()

    def _prepare_folders(self, cron_timeout):
        """
        --- RELATES ONLY TO THE RULES OF TYPE 'model' ---
        The method to parse automatic rules to trigger folders update:
         * recursive folder creation for each parent rule
         * deactivating obsolete folders related to the rules

        Args:
         * cron_timeout - datetime after which cron should be stopped

        Methods:
         *  _prepare_folder_recursively

        Returns:
         * bool - whether the method is fully done

        Extra info:
         * While parsing the rules we rely upon sequence of the rules. If a folder is found by the first rule, it would
           be excluded from the others
         * search of inactive records uses suboptimal ['id' not in] expression. However, at this point we have 
           only list of ids, while browsing over those leads to the same results 
        """
        self.env["clouds.client"]._cloud_log(True, "Folders update was started. Locked till: {}".format(cron_timeout))
        Config = self.env['ir.config_parameter'].sudo()
        # if there was a savepoint, get done rules and folders
        folders_savepoint = json.loads(Config.get_param("cloud_base_folders_savepoint", "{}"))
        done_sync_models_ids = []
        reconcilled_ids = []
        managed_dict = {}
        if folders_savepoint != "{}":
            done_sync_models_ids = folders_savepoint.get("synced_models_list", [])
            reconcilled_ids = folders_savepoint.get("reconcilled_ids", [])
            managed_dict = folders_savepoint.get("managed_dict", {})
        # go by rules recursively
        to_sync_models = self.search([("parent_id", "=", False), ("rule_type", "=", "model")])
        for s_model in to_sync_models:
            reconcilled_ids, done_sync_models_ids, fully_done = s_model._prepare_folders_recursively(
                cron_timeout, False, [], reconcilled_ids, done_sync_models_ids, managed_dict,
            )
            done_sync_models_ids.append(s_model.id)
            if not fully_done:
                log_message = "Folders update was stopped because of timeout. Continue afterward"
                self.env["clouds.client"]._cloud_log(True, log_message, "WARNING")
                return False
        else:
            # if all rules are processed > deactivate folders which do not suit any of the rules
            # IMPORTANT: rule-related folders are created only here; so we may safely rely upon reconcilled items
            obsolete_folder_ids = self.env["clouds.folder"].search([
                ("id", "not in", reconcilled_ids), ("rule_id", "!=", False), ("rule_id.rule_type", "=", "model")
            ]) 
            obsolete_folder_ids.write({"active": False})
            Config.set_param("cloud_base_folders_savepoint", "{}")
            self.env["clouds.client"]._cloud_log(True, "Folders update was successfully finished")  
            self._cloud_commit()
            return True         

    def _prepare_folders_recursively(self, cron_timeout, parent_id=False, domain=[], reconcilled_ids=[], 
                                     done_sync_models_ids=[], managed_dict={}):
        """
        The method to prepare folder for this sync model and its records
        Trigger itself to launch the same for child sync models

        Args:
         * cron_timeout - datetime after which cron should be stopped
         * parent_id - int - id of clouds.folder object
         * domain - list (revers polish notation)
         * reconcilled_ids - list of ids - created clouds.folder (used both as argument and in return)
         * done_sync_models_ids - list if ids - sync rules which have been already processed
         * managed_dict - dict of id: list of ints; id - of sync rules; list - of clouds.folders ids which 
           child rules should be processed

        Methods:
         * _return_sync_domain
         * _reconcile_folder
         * _prepare_folder_names
         * _create_default_folders (recursion)

        Returns:
         * tuple
           ** list of ints - reconcilled ids of folders
           ** list of ints - done synced rules
           ** bool - whether this rule is fully processed or exited in the middle

        Extra info:
         * We do not control the type of rule there, since assume that different types of rules could not be in 
           hierarchy to each other. Actually a parent might be defined as a model-related rule only
         * We check for model even required in XML and ondelete cascade, since it might result in critical scenario,
           while controlling app deinstallation is not possible
         * We split the method into 2 loops to achieve the goals: (a) of performance: multi create is faster
           (b) to allow commit before getting to child rules
         * We split folders preparation for 2 goals: (a) to adapt for not optimal Postgres performance (avoid
           too big queries); (b) to commit and check timeouts
         * Expected singleton
        """
        if self.id in done_sync_models_ids:
            # processed by previous not finished cron job > might safely switch to a new rule
            return reconcilled_ids, done_sync_models_ids, True
        Config = self.env['ir.config_parameter'].sudo()
        s_model = self.model
        if s_model:
            rule_id_int = self.id 
            rule_id_sequence = self.sequence
            # manage this sync.model folder
            root_folder_id, create_vals, folder_write = self.env["clouds.folder"]._reconcile_folder({
                "name": self.name, 
                "rule_id": rule_id_int, 
                "parent_id": parent_id, 
                "active": True, 
                "res_model": s_model,
            })
            if root_folder_id:
                root_folder_id_int = root_folder_id.id
            else:
                root_folder_id_int = self.env["clouds.folder"].create(create_vals).id
            if root_folder_id_int not in reconcilled_ids:
                reconcilled_ids.append(root_folder_id_int)
            # manage folders of each object which relates to this sync.model
            s_domain = domain + self._return_sync_domain()
            s_model_records = self.env[s_model].search(s_domain) # all active (!) Odoo objects which suit filters
            default_folders = json.loads(self.default_folders) # list of default words to be created
            managed_folder_ids = self.env["clouds.folder"] # folders to trigger child rules
            managed_dict_list = managed_dict.get(str(self.id))
            if managed_dict_list:
                # folders which child rules should be processed kept in savepoint
                managed_folder_ids = self.env["clouds.folder"].search([("id", "in", managed_dict_list)])
            # split records in batches to be able to exit if timeouted and commit changes frequently
            while s_model_records:
                loop_records = s_model_records[:OBJECTS_TO_PROCESS]
                create_vals_list = [] # for performance we make multi create
                updated_folder_ids = self.env["clouds.folder"] # folders which attachments should be checked for update 
                names_formal = self._prepare_folder_names(loop_records) # dict of id: name
                for s_model_record in loop_records:
                    s_model_record_id = s_model_record.id
                    fol_name = names_formal.get(s_model_record_id) or s_model_record.name_get()[0][1]
                    subfolder_id, create_vals, folder_write = self.env["clouds.folder"]._reconcile_folder({
                        "name": fol_name,
                        "rule_id": rule_id_int,
                        "parent_id": root_folder_id_int,
                        "active": True,
                        "res_model": s_model,
                        "res_id": s_model_record_id,
                        "sequence": rule_id_sequence,
                    }, reconcilled_ids)
                    if subfolder_id:
                        subfolder_id_int = subfolder_id.id
                        if subfolder_id_int not in reconcilled_ids:
                            reconcilled_ids.append(subfolder_id.id)
                        managed_folder_ids += subfolder_id
                        if folder_write:
                            updated_folder_ids += subfolder_id
                    if create_vals:
                        create_vals_list.append(create_vals)
                else:
                    if create_vals_list:
                        new_folder_ids = self.env["clouds.folder"].create(create_vals_list)
                        if default_folders:
                            new_folder_ids._create_default_folders(default_folders)
                        managed_folder_ids += new_folder_ids
                        reconcilled_ids += new_folder_ids.ids
                        updated_folder_ids += new_folder_ids
                # Update attachments if folder was updated or just created
                res_model_attachment_ids = self.env["ir.attachment"].search([("res_model", "=", s_model)])
                for updated_folder in updated_folder_ids:
                    attachments_to_update = res_model_attachment_ids.filtered(
                        lambda atta: atta.res_id == updated_folder.res_id and atta.clouds_folder_id != updated_folder
                    ) 
                    if attachments_to_update:             
                        attachments_to_update.with_context(no_folder_update=True).write(
                            {"clouds_folder_id": updated_folder.id}
                        )
                # If not enough time left > make emergent exit
                if fields.Datetime.now() >= cron_timeout:
                    folder_savepoint_vals = json.dumps({
                        "synced_models_list": done_sync_models_ids,
                        "reconcilled_ids": reconcilled_ids,
                        "managed_dict": {self.id: managed_folder_ids.ids},
                    })
                    Config.set_param("cloud_base_folders_savepoint", folder_savepoint_vals)
                    self._cloud_commit()
                    return reconcilled_ids, done_sync_models_ids, False
                self._cloud_commit()
                s_model_records -= loop_records
 
            for child in self.child_ids:
                # we do not save rule or its child to done models since the same rule might be looped in super parent
                for m_folder_id in managed_folder_ids:
                    sub_domain = [(child.parent_field, "=", m_folder_id.res_id)]
                    reconcilled_ids, done_sync_models_ids, fully_done = child._prepare_folders_recursively(
                        cron_timeout, m_folder_id.id, sub_domain, reconcilled_ids, done_sync_models_ids, managed_dict,
                    )
                    if not fully_done:
                        return reconcilled_ids, done_sync_models_ids, False
            return reconcilled_ids, done_sync_models_ids, True

    def _prepare_folder_names(self, odoo_records):
        """
        The method to generate name for a newly created folder:
        The idea is to try to parse title based on sync model name_expression rule. Otherwise, we use name_get()

        Args:
         * odoo_records - recordset of Odoo instances of a certain class

        Methods:
         * _render_template of mail.template

        Returns:
         * dict of {id: title values}

        Extra info:
         * It is important to make rendering for all folders of the same rule simultaneously, since it is much faster
           than doing by each record
         * _render_template has own try/except, so we should not check it here
         * in the most cases rendering would fail for each record so we can here generate name_get dict as well
           Otherwise (if particular object template failed), a record name_get would be done in the loop of the
           parent method
        """
        names_formal = {}
        name_expression = self.name_expression
        if name_expression:
            names_formal = self.env["mail.template"]._render_template(name_expression, self.model, odoo_records.ids)
        if not names_formal:
            names_get_list = odoo_records.name_get()
            for name_tuple in names_get_list:
                names_formal.update({name_tuple[0]: name_tuple[1]})
        return names_formal

    def _return_sync_domain(self):
        """
        The method to return sync domain

        Methods:
         * _return_period_domain_and_title

        Returns:
         * list - Reverse Polish Notation

        Extra info:
         * We do not use the computed fields to avoid concurrent update
         * Expected singleton
        """
        self.ensure_one()
        period_domain, period_title = self._return_period_domain_and_title()
        result_domain = safe_eval(self.domain) + period_domain
        return result_domain

    def _return_period_domain_and_title(self):
        """
        The method to construct period domain and title

        Returns:
         * list - Reverse Polish Notation
         * char

        Methods:
         * _return_translation_for_field_label

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        merged_periods = {}
        for period in self.period_ids:
            field = self._return_translation_for_field_label(field=period.field_id)
            if merged_periods.get(field):
                or_str = _("or")
                merged_periods[field] = {
                    "domain": ['|'] + merged_periods[field]["domain"] + safe_eval(period.domain),
                    "title": u"{} {} {}".format(merged_periods[field]["title"], or_str,  period.title)
                }
            else:
                merged_periods[field] = {
                    "domain": safe_eval(period.domain),
                    "title": period.title,
                }
        domain = []
        title = ""
        for field, values in merged_periods.items():
            domain += values["domain"]
            title += "{}: {}; ".format(field, values["title"])
        return domain, title

    def _return_translation_for_field_label(self, field):
        """
        The method to return translation for field label

        Args:
         * field - ir.model.fields object

        Returns:
         * char
        """
        lang = self._context.get("lang") or self.env.user.lang
        return  field.with_context(lang=lang).field_description

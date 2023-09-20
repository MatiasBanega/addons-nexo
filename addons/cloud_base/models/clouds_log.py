# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

LOGS_LIMIT = 500

class clouds_log(models.Model):
    """
    The class to represent each particular operation result
    The idea is to create some view by dates which would include all results of operations for this date with export
    features
    """
    _name = "clouds.log"
    _description = "Sync Logs"

    name = fields.Datetime(string="Log time", required=True,)
    log_date = fields.Date(string="Log date", required=True,)
    client_name = fields.Char(string="Client name")
    client_id = fields.Char(string="Client ID")
    log_type = fields.Char(string="Log type")
    logs = fields.Text(string="Logs", default="",)

    _order = "name DESC,id DESC" # within a day logs go from oldest to newest by time 

    @api.model
    def action_prepare_logs_html(self, log_args={}, search_domain=[], selected_clients=[]):
        """
        The method to render cloud logs as HTML and with filters specified in args

        Args:
         * log_args - dict of possible search criteria:
           ** last_log - int - from which log to consider
           ** first_log - int - to which log to consider
         * search_domain - list - RPR notation of current search criteria 
         * selected_clients - list of ints
        
        Methods:
         * _search_logs_by_params
         * _represent_as_html

        Returns:
         * log_args - dict
          ** string 
          ** last_log - int - last cloud_log taken (to control further js refreshing)
          ** first_log - int - the first cloud_log taken (to apply 'load more' before that)
          ** load_more_btn - bool - True if there are logs which might be loaded previously according to the 
             current filters
         * search_domain - list - RPR notation
         * selected_clients - list of integers

        Extra info:
         * the method critically depends on order of logs
        """
        log_ids = self._search_logs_by_params(log_args, search_domain, selected_clients, True)
        load_more_btn = len(log_ids) > LOGS_LIMIT and True or False
        if load_more_btn:
            log_ids = log_ids[:-1]
        log_html = ""
        for log in log_ids:
            log_html = log._represent_as_html() + log_html       
        last_log = log_ids and log_ids[0].id or False
        first_log = log_ids and log_ids[-1].id or False
        return {
            "log_html": log_html, 
            "last_log": last_log, 
            "first_log": first_log,
            "load_more_btn": load_more_btn,
        } 

    @api.model
    def action_open_tasks(self, selected_clients=[], only_blocked=False):
        """
        The method top open clouds queue related to selected clients
        
        Args:
         * selected_clients - list of chosen clients
         * only_blocked - bool (True if to show only failed tasks)

        Returns:
         * action dict
        """
        action_id = self.env.ref("cloud_base.clouds_queue_action").read()[0]
        s_domain = only_blocked and [("fail_num", "!=", 0)] or []
        if selected_clients:
            selected_clients_int = [int(cli) for cli in selected_clients if cli.isdigit()]
            s_domain += [("client_id", "in", selected_clients_int)]
        action_id["domain"] =  s_domain
        action_id["views"] = [(False, 'list'), (False, 'form')]
        return action_id

    @api.model
    def _cloud_log(self, client_name, client_id, result, client_mes, log_type=False):
        """
        The method to add a definite line for logs

        Args:
         * client_name - char - related clouds.client name
         * client_uid - int - related clouds.client integer
         * result - bool - if operation was successful or not
         * client_mes - char - string - what has happened with explanations
         * log_type - char - if log has a specific, not result-related level, e.g. 'DEBUG'

        Extra info:
         * Expected singleton
        """
        if not log_type:
            log_type = result and "INFO" or "ERROR"   
        log_vals ={
            "name": fields.Datetime.now(),
            "log_date": fields.Date.today(),
            "client_name": client_name,
            "client_id": client_id,
            "log_type": log_type,
            "logs": client_mes,            
        }
        self.create(log_vals)     
    
    @api.model
    def _prepare_txt_logs(self, search_domain=[], selected_clients=[]):
        """
        The method to prepare logs as simple text

        Args:
         * search_domain - list - RPR notation
         * selected_clients - list of integers

        Returns:
         * text         
        """
        log_ids = self._search_logs_by_params({}, search_domain, selected_clients, False)
        log_text = ""
        for log in log_ids:
            log_text = log._represent_as_text() + log_text 
        return log_text

    @api.model
    def _search_logs_by_params(self, log_args={}, search_domain=[], selected_clients=[], search_limit=False):
        """
        The method to find logs by params

        Args:
         * log_args - dict
          ** string 
          ** last_log - int - last cloud_log taken (to control further js refreshing)
          ** first_log - int - the first cloud_log taken (to apply 'load more' before that)
          ** load_more_btn - bool - True if there are logs which might be loaded previously according to the 
             current filters
         * search_domain - list - RPR notation
         * selected_clients - list of integers
 
        Returns:
         * cloud.log recordset
        """
        domain = []
        if log_args.get("last_log"):
            last_object = self.browse(log_args.get("last_log")).exists()
            if last_object:
                domain += [
                    "|", 
                        ("name", ">", last_object.name), 
                        "&", # to make sure simultaneous logs would appear
                            ("name", "=", last_object.name),
                            ("id", ">", last_object.id)
                ]
        if log_args.get("first_log"):
            first_object = self.browse(log_args.get("first_log")).exists()
            if first_object:
                domain += [
                    "|",
                        ("name", "<", first_object.name),
                        "&", # to make sure simultaneous logs would appear
                            ("name", "=", first_object.name),
                            ("id", "<", first_object.id)
                ]
        if search_domain:
            domain += search_domain
        if selected_clients:
            domain += [("client_id", "in", selected_clients)]
        if search_limit:
            log_ids = self.search(domain, limit=LOGS_LIMIT+1)
        else:
            log_ids = self.search(domain)
        return log_ids

    @api.model
    def get_cloud_clients(self, selected_clients=[]):
        """
        The method to retrieve the list of confirmed cloud clients and their states

        Args:
         * selected_clients - list of chosen clients

        Returns:
         * list of dicts
          ** id - int
          ** name - char
          ** state - char 
          ** title - char
          ** chosen - bool
        """
        result = [{
            "id": "CORE",
            "name": "General sync",
            "state": "success",
            "title": _("General sync logs"),  
            "chosen": "CORE" in selected_clients,      
        }]
        client_ids = self.env["clouds.client"].with_context(active_test=False).search([])
        if client_ids:
            result += client_ids.mapped(lambda cli: {
                "id": cli.id,
                "name": cli.name,
                "state": cli.error_state and "danger" or not cli.active and "muted" \
                         or cli.state in ["reconnect", "draft"] and "warning" or "success",
                "title": cli.error_state or not cli.active and _("Awaiting reverse sync") or cli.state == "reconnect" \
                         and _("Awaiting reconnection") or cli.state == "draft" and _("Awaiting confirmation") or "",
                "chosen": str(cli.id) in selected_clients,
            })
        return result

    @api.model
    def get_cloud_queue(self, selected_clients=[]):
        """
        The method to retrieve the list of confirmed cloud clients and their states

        Args:
         * selected_clients - list of chosen clients

        Returns:
         * dict of
          ** active_tasks - int
          ** failed_tasks - int
        """
        s_domain = []
        if selected_clients:
            selected_clients_int = [int(cli) for cli in selected_clients if cli.isdigit()]
            s_domain += [("client_id", "in", selected_clients_int)]
        active_tasks = self.env["clouds.queue"].search_count(s_domain)
        s_domain.append(("fail_num", "!=", 0))
        failed_tasks = self.env["clouds.queue"].search_count(s_domain)
        return {
            "active_tasks": active_tasks,
            "failed_tasks": failed_tasks,
        }

    def _represent_as_html(self):
        """
        The method to prepare a log as HTML

        Returns:
         * string

        Extra info:
         * Expected singleton (but with no ensure_one for performance reasons)
        """
        self = self.sudo()
        datetime_part = "<span class='cloud_logs_time'>{}</span>".format(self.name)
        log_type_part = "<span class='cloud_logs_level cloud_logs_{}'>{}</span>".format(self.log_type, self.log_type)
        client_part = "<span class='cloud_logs_client'>[{}#{}]</span>".format(
            self.client_name, self.client_id
        )
        log_message = "<div class='cloud_logs_unit'>{} {} {} {}</div>".format(
            datetime_part, log_type_part, client_part, self.logs
        )
        return log_message

    def _represent_as_text(self):
        """
        The method to prepare a log as HTML

        Returns:
         * string

        Extra info:
         * Expected singleton (but with no ensure_one for performance reasons)
        """
        self = self.sudo()
        log_message = "{} {} [{}#{}] {}\n".format(
            self.name, self.log_type, self.client_name, self.client_id, self.logs
        )
        return log_message

# -*- coding: utf-8 -*-

import logging
import mimetypes

from odoo import api, fields, models

from ..libs.dropbox_service import Client, ClientTeam, DropboxOAuth2Flow

_logger = logging.getLogger(__name__)


SCOPES = ["files.metadata.write", "files.content.read", "files.content.write", "sharing.write"]
TEAMEXTRASCOPES = ["team_data.member", "members.read"]


class clouds_client(models.Model):
    """
    Overwrite to add Dropbox methods
    """
    _inherit = "clouds.client"

    def _default_dropbox_redirect_url(self):
        """
        The method to return default for dropbox_redirect_url
        """
        Config = self.env["ir.config_parameter"].sudo()
        base_odoo_url = Config.get_param("web.base.url", "http://localhost:8069") 
        return "{}/dropbox_token".format(base_odoo_url)

    cloud_client = fields.Selection(
        selection_add=[("dropbox", "Dropbox")],
        required=True,
        ondelete={"dropbox": "cascade"},
    )
    dropbox_app_key = fields.Char(
        string="Dropbox app key",
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    dropbox_app_secret = fields.Char(
        string="Dropbox app secret",
        readonly=True,
        states={'draft': [('readonly', False)], 'reconnect': [('readonly', False)]},
    )
    dropbox_redirect_url = fields.Char(
        string="Dropbox redirect URL",
        default=_default_dropbox_redirect_url,
        readonly=True,
        states={'draft': [('readonly', False)], 'reconnect': [('readonly', False)]},
        help="The same redirect url should be within your Dropbox app settings",
    )
    dropbox_team = fields.Boolean(
        string="Dropbox team",
        states={'draft': [('readonly', False)]},
        help="Check, if sync should be done for the Dropbox team account",
    )
    dropbox_no_links = fields.Boolean(
        string="No links to Dropbox from Odoo",
        help="""
            If checked, you would not be able to open a Dropbox file or Dropbox folder from Odoo
            There might be 2 reasons for that:
             1. Personal Dropbox (Free, Plus, Professional plans) makes public links for all Odoo-related folders and
                files. It is not fully safe.
                Although website urls will be hardly known by external users, there is a slight chance that
                they become available as a result of some user actions
             2. You would like to speed sync up. During both direct and backward sync, Odoo tries to retrieve
                updated urls of each Dropbox Odoo-related item. It results in a significant number of requests,
                what might make the process slow.
        """,
    )
    dropbox_admin = fields.Char(
        string="Dropbox admin email",
        help="Under this user all files and folders would be created, changed and deleted in Dropbox",
    )
    dropbox_refresh_token = fields.Char(
        string="Dropbox active token",
        readonly=True,
        default="",
    )

    def action_dropbox_establish_connection(self):
        """
        The method to establish connection for Dropbox

        Methods:
         * gd_get_auth_url

        Returns:
         * action window to confirm in Dropbox
        
        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        auth_url, log_message = self._drb_get_auth_url()
        if auth_url:
            self.error_state = False
            res = {
                'name': 'Dropbox',
                'type': 'ir.actions.act_url',
                'url': auth_url,
            }
        else:
            self.error_state = log_message
            res = self.env.ref('cloud_base.clouds_client_action_form_only').read()[0]
            res["res_id"] = self.id
        return res

    ####################################################################################################################
    ##################################   LOG IN METHODS ################################################################
    ####################################################################################################################    
    def _drb_get_auth_url(self):
        """
        The method to get URL to login in DropBox

        Methods: 
         * _cloud_log

        Returns:
         * tuple:
          ** str - target URL
          ** str - log message  

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        self._cloud_log(True, "App confirmation process was started", "DEBUG")
        scope = self.dropbox_team and TEAMEXTRASCOPES+SCOPES or SCOPES
        log_message = ""
        try:
            AUTH_FLOW = DropboxOAuth2Flow(
                consumer_key=self.dropbox_app_key,
                redirect_uri=self.dropbox_redirect_url, 
                session={}, 
                csrf_token_session_key="dropbox_refresh_token_{}".format(self.id), 
                consumer_secret=self.dropbox_app_secret,
                token_access_type="offline", 
                scope=scope,
            )
            auth_url = AUTH_FLOW.start()
            log_message = "App confirmation URL was received"
        except Exception as e:
            auth_url = False
            log_message = "Could not start app confirmation. Reason: {}".format(e)
        self._cloud_log(auth_url and True or False, log_message)
        return auth_url, log_message

    def _drb_finish_auth(self, query_params):
        """
        The method to receive refresh token from Dropbox response

        Args:
         * query_params - what we have received from Dropbox

        Methods:
         * _return_specific_client_context
         * _dropbox_root_directory
         * _cloud_log

        Returns:
         *BBool - true if succeced
         * char

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        log_message = ""
        try:
            scope = self.dropbox_team and TEAMEXTRASCOPES+SCOPES or SCOPES
            recreatedFlow = DropboxOAuth2Flow(
                consumer_key=self.dropbox_app_key,
                redirect_uri=self.dropbox_redirect_url, 
                session={"dropbox_refresh_token_{}".format(self.id): query_params.get("state")}, 
                csrf_token_session_key="dropbox_refresh_token_{}".format(self.id), 
                consumer_secret=self.dropbox_app_secret,
                token_access_type="offline", 
                scope=scope,
            )
            auth_result = recreatedFlow.finish(query_params)
            self._cloud_log(True, "Finishing app confirmation", "DEBUG")
        except Exception as er:
            log_message = "Could not finish authentication. Reason: {}".format(er)
            self._cloud_log(False, log_message)
            return False, log_message                    
        # this should be written already now, since needed for further methods
        self.dropbox_refresh_token = auth_result.refresh_token
        ctx = self.env.context.copy()
        this_client_ctx = self._return_specific_client_context()
        if not this_client_ctx.get("cclients"):
            log_message = "Could not finish authentication since client could not be initiated"
            self._cloud_log(False, log_message)
            return False, log_message             
        ctx.update(this_client_ctx)
        root_dir = self.with_context(ctx)._dropbox_root_directory()
        if root_dir:
            self.write({"dropbox_refresh_token": auth_result.refresh_token, "state": "confirmed"})
            log_message = "App confirmation was finished"
            self._cloud_log(True, log_message)
            return True, log_message
        else: 
            log_message = "App confirmation was not finished. Root folder could not be created. Check logs"
            self._cloud_log(False, log_message)
            return False, log_message

    ####################################################################################################################
    ##################################   API methods   #################################################################
    ####################################################################################################################    
    def _dropbox_get_client(self):
        """
        Method to return instance of wrapped Dropbox Instance

        Methods:
         * _cloud_log

        Returns:
         * tuple
          ** Dropbox instance if initiated. False otherwise
          ** char  

        Extra info:
         * Expected singleton
        """
        log_message = ""
        try:
            if self.dropbox_team:
                admin = self.dropbox_admin
                team_client = ClientTeam(
                    app_key=self.dropbox_app_key, 
                    app_secret=self.dropbox_app_secret, 
                    oauth2_refresh_token=self.dropbox_refresh_token,
                    scope=TEAMEXTRASCOPES+SCOPES
                )
                members_res = team_client.team_members_list()
                members = members_res.members
                while members_res.has_more:
                    members_res = team_client.team_members_list_continue(cursor=members_res.cursor)
                    members += members_res.entries
                admin_user = [member.profile.team_member_id for member in members if member.profile.email == admin]
                if admin_user:
                    res_client = team_client.as_user(team_member_id=admin_user[0])
                    log_message = "Team client was authenticated"
                else:
                    res_client = False
                    log_message = "No user was found among {} for the admin user {}. Enter another user".format(
                        members, admin
                    )
            else:
                res_client = Client(
                    app_key=self.dropbox_app_key, 
                    app_secret=self.dropbox_app_secret,
                    oauth2_refresh_token=self.dropbox_refresh_token,
                    scope=SCOPES
                )
                log_message = "Client was authenticated"
        except Exception as er:
            res_client = False
            log_message = "Client was not initiated. Reason: {}".format(er)
        self._cloud_log(res_client and True or False, log_message)
        try:
            # to forbid showing any 'dropbox' loggers except Error & CRITCIAL ones
            res_client._logger.setLevel(logging.ERROR)
        except Exception as er:
            self._cloud_log(False, "Could not turn off Dropbox logging: {}".format(er), "WARNING")
        return res_client, log_message

    def _dropbox_check_root_folder(self, client_id):
        """
        The method to check whether the root folder exists

        Args:
         * client_id - instance of DropBox Client

        Methods:
         * files_get_metadata of DropBox Client
        
        Returns:
         * True 

        Extra info:
         * IMPORTANT NOTE: here client is passed in args, not in context, since context is not yet updated
         * Expected singleton 
        """
        self.ensure_one()
        log_message = ""
        res = True
        odoo_path = client_id.files_get_metadata(self.root_folder_key)
        if not odoo_path:
            res = False
            child_items = {}
            log_message = "The root folder is not available. To create a new one: re-connect"
        return res, log_message

    def _dropbox_check_api_error(self, error):
        """
        The method to get an error type based on response
            
        Args:
         * error class related to API

        Retunes:
         * int
        """
        error_type = 400
        if type(error).__name__ == "ApiError":
            checked_error = error.error
            if type(checked_error).__name__ == "GetMetadataError":
                if checked_error.is_path() and checked_error.get_path().is_not_found():
                    # when create a folder (metadata firstly received)
                    # GetMetadataError('path', LookupError('not_found', None))
                    error_type = 404
            elif type(checked_error).__name__ == "DeleteError":
                if checked_error.is_path_lookup() and checked_error.get_path_lookup().is_not_found():
                    # when delete a file
                    # DeleteError('path_lookup', LookupError('not_found', None))
                    error_type = 404
            elif type(checked_error).__name__ == "ListFolderError":
                if checked_error.is_path() and checked_error.get_path().is_not_found():
                    # when get children of folder
                    # ListFolderError('path', LookupError('not_found', None)
                    error_type = 404
            elif type(checked_error).__name__ == "RelocationError":
                if checked_error.is_from_lookup() and checked_error.get_from_lookup().is_not_found():
                    # when move/update file or folder
                    # RelocationError('from_lookup', LookupError('not_found', None))
                    error_type = 404
        elif type(error).__name__ == "ValidationError" and "did not match pattern" in error.message:
            # extreme scenario when cloud_key is for strange reasons is considered by dropbox as path
            error_type = 404
        return error_type

    def _dropbox_wrap_metadata(self, metadata):
        """
        The method to wrap metadata received from Dropbox into cloud_base dict accepted by all methods
        Examples of meta data:
        >>  Meta Data format: FolderMetadata(
                name='Odoo',
                id='id:x7e9gMT5k7AAAAAAAAAAGQ',
                path_lower='/odoo',
                path_display='/Odoo',
                parent_shared_folder_id=None,
                shared_folder_id=None,
                sharing_info=None,
                property_groups=None,
            )
        >>  FileMetadata(
                client_modified=datetime.datetime(2021, 7, 21, 15, 1, 11), 
                content_hash='fb323a994246b8ab4d412e8e5a457d985f7bd4d27c06335cb9318621509fd637', 
                export_info=NOT_SET, 
                file_lock_info=NOT_SET, 
                has_explicit_shared_members=NOT_SET, 
                id='id:_1knmJ0VYg4AAAAAAAACPg', 
                is_downloadable=True, 
                media_info=NOT_SET, 
                name='FAQ_modified.docx', 
                parent_shared_folder_id=NOT_SET, 
                path_display='/Odoo/A/dropbox created/FAQ_modified.docx', 
                path_lower='/odoo/a/dropbox created/faq_modified.docx', 
                property_groups=NOT_SET, 
                rev='015c7a370e9cf59000000022dc41620', 
                server_modified=datetime.datetime(2021, 7, 21, 15, 1, 11), 
                sharing_info=NOT_SET, 
                size=18136, 
                symlink_info=NOT_SET
            )

        Args:
         * metadata - instance of Dropbox client metadata

        Methods:
         * get_team_link_d
         * _cloud_log

        Returns:
         * dict if metadata was instance
         * list of dicts if it was instances

        Extra info:
         * the method does not return mimetype regretfully, so we apply that only for folders
        """
        client = self._context.get("cclients", {}).get(self.id)
        if self.dropbox_no_links:
            # this url will hardly work in the most cases
            url = u"https://www.dropbox.com/home/{}".format(metadata.path_lower)
        else:
            try:
                url = client.get_team_link_d(path=metadata.path_lower, team=self.dropbox_team)
            except Exception as error:
                url = metadata.name
                log_message = "The url for '{}' was not received. Error: {}".format(metadata.name, error)
                self._cloud_log(False, log_message, "WARNING")
        res = {
            "id": metadata.id,
            "name": metadata.name,
            "url": url,
            "path": metadata.path_lower,
        }
        if type(metadata).__name__ == "FolderMetadata":
            res.update({"mimetype": "dir"})
        return res

    def _dropbox_wrap_metadata_list(self, metadata):
        """
        The method to wrap list of metadata received from DropBox into cloud_base dict acceptedby all methods

        Args:
         * metadata - instance of DropBox Client Metadata
         * client - DropBox Client

        Methods:
         * _dropbox_wrap_metadata

        Returns:
         * list of dicts if it was instances
        """
        return [self._dropbox_wrap_metadata(data) for data in metadata]

    def _dropbox_root_directory(self):
        """
        Method to return root directory name and id (create if not yet)

        Methods:
         * _check_api_error
         * files_get_metadata of Dropbox client
         * files_create_folder_v2 of Dropbox client
         * _cloud_log

        Returns:
         * bool - True if the root folder was created / found successfully
        """
        client = self._context.get("cclients", {}).get(self.id)
        res_id = self.root_folder_key
        res = False
        if res_id:
            try:
                #in try, since the folder might be removed in meanwhile
                res = client.files_get_metadata(res_id)
                self._cloud_log(True, "Root directory {},{} was successfully found".format(
                    self.root_folder_name, self.root_folder_key
                ))
            except Exception as error:
                if self._check_api_error(error) == 404:
                    res_id = False # to guarantee creation of item
                    self._cloud_log(
                        False, 
                        "Root directory {}{} was removed in clouds. Creating a new one".format(
                            self.root_folder_name, self.root_folder_key
                        ),
                        "WARNING",
                    )
                else:
                    self._cloud_log(False, "Unexpected error while searching root directory {},{}: {}".format(
                        self.root_folder_name, self.root_folder_key, error
                    ))
                    res_id = True # to guarantee no creation of item
                    res = False
        if not res_id:
            try:
                root_path = "/{}".format(self.root_folder_name)
                res_id = client.files_create_folder_v2(root_path).metadata
                self.root_folder_key = res_id.id
                res = res_id
                self._cloud_log(True, "Root directory {} was successfully created".format(self.root_folder_name))
            except Exception as error:
                res = False
                self._cloud_log(
                    False, 
                    "Unexpected error during root directory {} creation: {}".format(self.root_folder_name, error)
                )
        return res and True or False

    def _dropbox_api_get_child_items(self, cloud_key=False):
        """
        The method to retrieve all child elements for a folder
        Note: If folder was removed, all its children were removed as well

        Args:
         * cloud_key - char

        Methods:
         * files_list_folder_d of Dropbox API Client
         * _dropbox_wrap_metadata_list

        Returns:
         * dicts:
          ** folder_ids
          ** attachment_ids
          Each has keys:  
           *** cloud_key - char (cloud key)
           *** name - char
        """ 
        client = self._context.get("cclients", {}).get(self.id)
        items = self._dropbox_wrap_metadata_list(client.files_list_folder_d(cloud_key, recursive=False))
        attachments = []
        subfolders = []
        for child in items:
            res_vals = {"cloud_key": child.get("id"),"name": child.get("name"),}
            if child.get("mimetype") == "dir":
                subfolders.append(res_vals)
            else:
                attachments.append(res_vals)
        return {"folder_ids": subfolders, "attachment_ids": attachments} 

    def _dropbox_download_by_cloud_key(self, cloud_key):
        """
        The method to get binary content from clouds
        Introduced to be possible to donwload binary by a single arg - cloud_key
        So, it becomes more universal than pre-defined _dropbox_upload_attachment_from_cloud 

        Args:
         * cloud_key - char

        Methods:
         * files_download of Dropbox API Client
         * files_download_zip
        
        Returns:
         * binary or False
        """
        client = self._context.get("cclients", {}).get(self.id)
        try:
            md, result = client.files_download(cloud_key)
        except:
            md, result = client.files_download_zip(cloud_key)
        return result and result.content or False

    def _dropbox_upload_attachment_from_cloud(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to upload a file from cloud

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _dropbox_download_by_cloud_key

        Returns:
         * binary (base64 decoded)
        """
        return self._dropbox_download_by_cloud_key(attachment_id.cloud_key)

    def _dropbox_get_full_path(self, cloud_key, new_item_name):
        """
        The method to retrieve topical path of a parent folder by key

        Args:
         * cloud_key - id of a parent item
         * new_item_name - char

        Methods:
         * files_get_metadata of Dropbox API Client
         * _build_path 
        
        Returns:
         * str
        """
        client = self._context.get("cclients", {}).get(self.id)
        parent_folder_path = client.files_get_metadata(cloud_key).path_lower
        path = self._build_path([parent_folder_path, new_item_name])
        return path

    def _dropbox_setup_sync(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create folder in clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 
         * args should contain 'parent_key'

        Methods:
         * _dropbox_get_full_path 
         * _dropbox_wrap_metadata
         * files_create_folder_v2 of Dropbox API Client

        Returns:
         * dict of values to write in clouds.folder

        Extra info:
         * setup sync assumes that a folder does not exist in client. If a folder was previously deactivated,
           it was just deleted from clouds
        """
        result =  False
        client = self._context.get("cclients", {}).get(self.id)
        path = self._dropbox_get_full_path(args.get("parent_key"), folder_id.name)
        result = self._dropbox_wrap_metadata(client.files_create_folder_v2(path, autorename=True).metadata)
        result = {
            "cloud_key": result.get("id"), 
            "url": result.get("url"),
        }
        return result

    def _dropbox_update_folder(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to update folder in clouds
       
        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 
         * in args we should receive parent_key

        Methods:
         * _dropbox_get_full_path
         * _dropbox_wrap_metadata
         * files_move_v2 of Dropbox API Client

        Returns:
         * dict of values to write in clouds folder
        """
        client = self._context.get("cclients", {}).get(self.id)
        new_path = self._dropbox_get_full_path(args.get("parent_key"), folder_id.name)
        result = self._dropbox_wrap_metadata(client.files_move_v2(
            folder_id.cloud_key,
            new_path,
            allow_shared_folder=True,
            autorename=True,
            allow_ownership_transfer=True,
        ).metadata)
        result = {
            "cloud_key": result.get("id"), 
            "url": result.get("url"),
        }
        return result

    def _dropbox_delete_folder(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to delete folder in clouds 
        The method is triggered directly from _adapt_folder_reverse (cloud_client does not have _delete_folder)
        UNDER NO CIRCUMSTANCES DO NOT DELETE THIS METHOD
       
        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 

        Methods:
         * files_delete_v2 of Dropbox API Client

        Returns:
          * bool  
        """
        result = False
        client = self._context.get("cclients", {}).get(self.id)
        result = client.files_delete_v2(folder_id.cloud_key)           
        return result and True or False

    def _dropbox_upload_file(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to upload file to clouds
        
        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 
         * args should contain attach_name

        Methods:
         * _dropbox_get_full_path
         * _full_path of ir.attachment
         * _dropbox_wrap_metadata
         * files_upload of Dropbox API Client

        Returns:
         * dict of values to write in ir.attachment

        Extra info:
         * IMPROTANT: autorename for files work only for DIFFRENT CONTENT
           So, it would be okay to have 2 different files with the same name, but having absolutely the same files
           would result in now new item. We consider that normal as backward sync would delete a repeated item as well 
        """
        client = self._context.get("cclients", {}).get(self.id)
        path = self._dropbox_get_full_path(folder_id.cloud_key, args.get("attach_name"))
        local_path = attachment_id._full_path(attachment_id.store_fname)
        with open(local_path, 'rb') as f:
            result = self._dropbox_wrap_metadata(client.files_upload(f.read(), path, autorename=True))
        result = {
            "cloud_key": result.get("id"),
            "url": result.get("url"),
            "store_fname": False,
            "type": "url",
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
        }
        return result

    def _dropbox_update_file(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to update file in clouds
       
        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 
         * Args should contain attach_name

        Methods:
         * _dropbox_get_full_path
         * _dropbox_wrap_metadata
         * files_move_v2 of Dropbox API Client


        Returns:
         * dict to write in attachment

        Extra info:
         * IMPROTANT: autorename for files work only for DIFFRENT CONTENT
           So, it would be okay to have 2 different files with the same name, but having absolutely the same files
           would result in now new item. We consider that normal as backward sync would delete a repeated item as well 
        """
        client = self._context.get("cclients", {}).get(self.id)
        new_path = self._dropbox_get_full_path(folder_id.cloud_key, args.get("attach_name"))
        result = self._dropbox_wrap_metadata(client.files_move_v2(
            attachment_id.cloud_key,
            new_path,
            allow_shared_folder=True,
            autorename=True,
            allow_ownership_transfer=True,
        ).metadata)
        result = {
            "cloud_key": result.get("id"), 
            "url": result.get("webViewLink"),
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
        }
        return result

    def _dropbox_delete_file(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to delete file in clouds
       
        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 

        Methods:
         * files_delete_v2 of Dropbox API Client

        Returns:
          * bool  
        """
        result = False
        client = self._context.get("cclients", {}).get(self.id)
        result = client.files_delete_v2(attachment_id.cloud_key)           
        return result and True or False

    def _dropbox_create_subfolder(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create clouds.folder in Odoo based on cloud client folder info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 

        Methods:
         * _dropbox_wrap_metadata
         * files_get_metadata of Dropbox API Client

        Returns:
          * dict of clouds.folder values 
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = self._dropbox_wrap_metadata(client.files_get_metadata(cloud_key))
        result = {
            "cloud_key": cloud_key,
            "name": cdata.get("name"),
            "parent_id": folder_id.id, 
            "own_client_id": self.id,
            "active": True,
            "url": cdata.get("url"),
        }
        return result

    def _dropbox_create_attachment(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create ir.attachment in Odoo based on cloud client file info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 

        Methods:
         * _dropbox_wrap_metadata
         * files_get_metadata of Dropbox API Client
         * guess_type from the lib mimetypes

        Returns:
          * dict of ir.attachment values

        Extra info:
         * dropbox api does not return mimetype in media, so we have to apply guess_mimetype
           we do that by name and url and hope for the best
           In case critical scenarios arise, we migth try to apply more advanced guessing by content through 
           applying the odoo tools method guess_mimetype for decoded binary (see base/ir_attachment/_compute_mimetype)         
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = self._dropbox_wrap_metadata(client.files_get_metadata(cloud_key))
        result = {
            "cloud_key": cloud_key,
            "name": cdata.get("name"),
            "url": cdata.get("url"),
            "clouds_folder_id": folder_id.id,
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
            "store_fname": False,
            "type": "url",
            "mimetype": mimetypes.guess_type(cdata.get("name"))[0] or mimetypes.guess_type(cdata.get("url"))[0] \
                        or 'application/octet-stream',
        }
        return result

    def _dropbox_change_attachment(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to write on ir.attachment in Odoo based on cloud client file info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 

        Methods:
         * _dropbox_wrap_metadata
         * files_get_metadata of Dropbox API Client

        Returns:
          * dict of ir.attachment values
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = self._dropbox_wrap_metadata(client.files_get_metadata(cloud_key))
        result = {
            "name": cdata.get("name"),
            "url": cdata.get("url"),
        }
        return result

    def _dropbox_attachment_reverse(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create ir.attachment in Odoo based on cloud client file info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base) 

        Methods:
         * _dropbox_wrap_metadata
         * files_get_metadata of Dropbox API Client
         * _dropbox_download_by_cloud_key

        Returns:
          * dict of ir.attachment values

        Extra info:
         * IMPORTANT: mimetype should NOT be written here, since we already do that in backward sync creation. 
           Otherwise, there might be conflicts
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = self._dropbox_wrap_metadata(client.files_get_metadata(cloud_key))
        # IMPORTANT: do not write clouds_folder_id. It would break attachments moves
        result = {
            "cloud_key": False,
            "name": cdata.get("name"),
            "url": False,
            "type": "binary",
            "sync_cloud_folder_id": False,
            "sync_client_id": False,
        }
        binary_content = self._dropbox_download_by_cloud_key(cloud_key)
        result.update({"raw": binary_content})
        return result

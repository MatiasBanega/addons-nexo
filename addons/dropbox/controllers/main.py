# -*- coding: utf-8 -*-

import werkzeug

from odoo import _
from odoo.http import Controller, route, request


class dropbox_token(Controller):
    """
    Dropbox controller to catch response from Dropbox API
    """   
    @route('/dropbox_token', type='http', auth='user', website='False')
    def login_to_dropbox(self, **kwargs):
        """
        Method that handles incoming token from Dropbox

        Methods:
         * _drb_finish_auth of clouds.client
         * _generate_cloud_client_url of clouds.client

        Returns:
         * related clouds view

        Extra info:
         * For the case not correct client is found (very rare case 2 db clients are launched simultaneously),
           the method _gd_create_session would result in a credentials error
        """
        ctx = request.env.context.copy()
        cloud_client_id = request.env["clouds.client"].search(
            [("state", "in", ["draft", "reconnect"]), ("method_key", "=", "dropbox")], 
            order="last_establish DESC", 
            limit=1,
        )
        if not cloud_client_id:
            return request.render("cloud_base.error_page", {"cloud_error": _("Client was not found")})
        success, log_message = cloud_client_id._drb_finish_auth(kwargs)
        cloud_url = cloud_client_id._generate_cloud_client_url()
        if not success:
            cloud_client_id.error_state = log_message         
        return werkzeug.utils.redirect(cloud_url)

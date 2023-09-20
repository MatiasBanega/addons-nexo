import json

from odoo import http
from odoo.http import request


class DownloadScheduleItems(http.Controller):
    @http.route(["/get_csv/<int:var>"], type="http", auth="user", website=True)
    def get_csv(self, var):
        values = {}

        data = request.env["ir.attachment"].sudo().search([("id", "=", int(var))])

        if data:
            values["success"] = True
            values["return"] = "Something"
        else:
            values["success"] = False
            values["error_code"] = 1
            values["error_data"] = "No data found!"

        return json.dumps(values)

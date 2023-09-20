import csv
import base64
from os.path import splitext
from io import StringIO, TextIOWrapper, BytesIO

from odoo import fields, models, api, _
from odoo.exceptions import UserError

OPT_HAS_HEADER = "headers"
OPT_SEPARATOR = "separator"
OPT_QUOTING = "quoting"
OPT_ENCODING = "encoding"

TEMPLATE = ["name", "product_id", "product_uom_id", "size"]


class ProjectScheduleItemsImport(models.TransientModel):
    _name = "project.schedule.items.download"
    _description = "Project Item download"

    project_type_id = fields.Many2one("project.type", "Project Type")
    product_id = fields.Many2one(
        "product.template",
        "Item Type",
        required=True,
        domain="[('is_project_item', '=', True), ('project_type_id', '=', project_type_id)]",
    )
    product_uom_id = fields.Many2one("uom.uom", "Unit of Measure")

    def download_file(self):
        # target_model = self.env['project.schedule.items']
        # field_names = {name: field.string for name, field in target_model._fields.items()}
        template_data = []
        for rec in TEMPLATE:
            if rec == "product_id":
                get_product_id = self.env["product.product"].search_read(
                    [("product_tmpl_id", "=", self.product_id.id)], ["id"]
                )
                if get_product_id:
                    template_data.append(get_product_id[0]["id"])
                else:
                    template_data.append("")
            elif rec == "product_uom_id":
                template_data.append(self.product_uom_id.id)
            else:
                template_data.append("")
        # write csv
        f = BytesIO()
        writer = csv.writer(f, delimiter=",")
        encoding = "utf-8"
        writer.writerow(TEMPLATE)
        writer.writerow(template_data)
        # create attachment
        datas = base64.encodestring(f.getvalue().encode(encoding))
        attachment = self.env["ir.attachment"].create(
            {
                "name": "Schedule_Item.csv",
                "datas": datas,
                "datas_fname": "Schedule_Item.csv",
            }
        )
        # print(attachment)
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": "/web/content/%s?download=true" % (attachment.id),
        }

        # print(template_data)
        # # f = StringIO()
        # with open('quotes.csv', 'w') as file:
        #     writer = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC, delimiter=',')

        # writer = csv.writer(f, delimiter=',')
        # encoding = 'utf-8'
        # writer.writerow(TEMPLATE)
        # writer.writerow(template_data)
        # # for row in data:
        # #     writer.writerow(row)
        # # create attachment
        # datas = base64.encodebytes(f.getvalue().encode(encoding))

    @api.onchange("product_id", "product_uom_id")
    def onchange_product_id(self):
        if self.product_id:
            # self.lots_visible = self.product_id.tracking != 'none'
            if not self.product_uom_id or self.product_uom_id.category_id != self.product_id.uom_id.category_id:
                self.product_uom_id = self.product_id.uom_id.id
            res = {"domain": {"product_uom_id": [("category_id", "=", self.product_uom_id.category_id.id)]}}
        else:
            res = {"domain": {"product_uom_id": []}}
        return res


class ProjectScheduleItemsImport(models.TransientModel):
    _name = "project.schedule.items.import"
    _description = "Project Item Import"

    data_file = fields.Binary(
        string="Schedule Item File",
        required=True,
        help="download template, or ask administrator for supported template",
    )
    filename = fields.Char()

    def import_file(self):
        """Process the file chosen in the wizard, create bank statement(s) and go to reconciliation."""
        self.ensure_one()
        project_id = self._context.get("project_id", False)
        project_schedule_items_ids = self.env["project.schedule.items"]
        if project_id:
            project_inst = self.env["project.project"].browse(int(project_id))
            if project_inst:
                schedule_fields, schedule_items_vals = self._read_csv_attachment(self.data_file)
                upload_rec = []
                for val in schedule_items_vals:
                    data = {}
                    skip_item = False
                    xy = 0
                    for v in TEMPLATE:
                        if v == "product_id":
                            # Check if product is related to project type

                            get_product_id = self.env["product.product"].search_read(
                                [("product_tmpl_id", "=", int(val[xy]))],
                                ["id", "product_tmpl_id"],
                            )
                            # if get_product_id:
                            #     product_rec = self.env['product.template'].browse(int(get_product_id[0]['product_tmpl_id'][0]))
                            #     if product_rec:
                            #         if product_rec.project_type_id.id != project_inst.type_id.id:
                            #             skip_item = True
                            if not skip_item:
                                data[v] = get_product_id[0]["id"]
                                xy += 1
                        else:
                            if not skip_item:
                                data[v] = val[xy]
                                xy += 1
                    if skip_item:
                        continue
                    upload_rec.append(data)
                # print(upload_rec)
                for rec in upload_rec:
                    rec["project_id"] = project_inst.id
                    project_schedule_items_ids.create(rec)
        return True

    def _read_csv_attachment(self, attachment):
        decoded_datas = base64.b64decode(attachment)
        encoding = "utf-8"
        f = TextIOWrapper(BytesIO(decoded_datas), encoding=encoding)
        reader = csv.reader(f, delimiter=",")

        fields = next(reader)
        data = [row for row in reader]
        return fields, data

    def _parse_file(self, data_file):
        """Each module adding a file support must extends this method. It processes the file if it can, returns super otherwise, resulting in a chain of responsability.
        This method parses the given file and returns the data required by the bank statement import process, as specified below.
        rtype: triplet (if a value can't be retrieved, use None)
            - currency code: string (e.g: 'EUR')
                The ISO 4217 currency code, case insensitive
            - account number: string (e.g: 'BE1234567890')
                The number of the bank account which the statement belongs to
            - bank statements data: list of dict containing (optional items marked by o) :
                - 'name': string (e.g: '000000123')
                - 'date': date (e.g: 2013-06-26)
                -o 'balance_start': float (e.g: 8368.56)
                -o 'balance_end_real': float (e.g: 8888.88)
                - 'transactions': list of dict containing :
                    - 'name': string (e.g: 'KBC-INVESTERINGSKREDIET 787-5562831-01')
                    - 'date': date
                    - 'amount': float
                    - 'unique_import_id': string
                    -o 'account_number': string
                        Will be used to find/create the res.partner.bank in odoo
                    -o 'note': string
                    -o 'partner_name': string
                    -o 'ref': string
        """
        raise UserError(
            _("Could not make sense of the given file.\nDid you install the module to support this type of file ?")
        )

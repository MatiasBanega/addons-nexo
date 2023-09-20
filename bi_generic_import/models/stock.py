# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import Warning, ValidationError
from odoo import models, fields, exceptions, api, _
import io
import tempfile
import binascii
import logging
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug("Cannot `import csv`.")
try:
    import xlwt
except ImportError:
    _logger.debug("Cannot `import xlwt`.")
try:
    import base64
except ImportError:
    _logger.debug("Cannot `import base64`.")
try:
    import xlrd
except ImportError:
    _logger.debug("Cannot `import xlrd`.")


class gen_inv_2(models.Model):
    _name = "generate.inv"

    product_counter_main = fields.Integer("Counter")

    @api.model
    def default_get(self, fields):
        res = super(gen_inv_2, self).default_get(fields)
        inv_id = self.env["generate.inv"].sudo().search([], order="id desc", limit=1)
        if inv_id:
            res.update({"product_counter_main": inv_id.product_counter_main})
        else:
            res.update({"product_counter_main": ""})
        return res


class gen_inv(models.TransientModel):
    _name = "gen.inv"

    file = fields.Binary("File")
    import_option = fields.Selection([("csv", "CSV File"), ("xls", "XLS File")], string="Select", default="csv")
    import_prod_option = fields.Selection(
        [("barcode", "Barcode"), ("code", "Code"), ("name", "Name")], string="Import Product By ", default="code"
    )
    is_validate_inventory = fields.Boolean(string="Validate Inventory")
    lot_option = fields.Boolean(string="Import Serial/Lot number with Expiry Date")
    location_id_option = fields.Boolean(string="Allow to Import Location on inventory line from file")

    def make_inventory_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        if date:
            try:
                i_date = datetime.strptime(str(date), DATETIME_FORMAT).date()
            except Exception:
                raise ValidationError(_("Wrong Date Format. Date Should be in format YYYY-MM-DD."))
            return i_date
        else:
            raise ValidationError(_("Date field is blank in sheet Please add the date."))

    def import_csv(self):

        """Load Inventory data from the CSV file."""
        if not self.file:
            raise ValidationError(_("Please Select File"))
        if self.import_option == "csv":

            data = base64.b64decode(self.file)
            try:
                file_input = io.StringIO(data.decode("utf-8"))
            except UnicodeError:
                raise ValidationError("Invalid file!")

            """Load Inventory data from the CSV file."""
            ctx = self._context
            if self.lot_option == True:
                keys = ["location", "code", "quantity", "date", "uom", "lot"]
            else:
                keys = ["location", "code", "quantity", "date", "uom"]
            stloc_obj = self.env["stock.location"]
            inventory_obj = self.env["stock.quant"]
            product_obj = self.env["product.product"]
            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=",")
            flag = 0

            generate_inv = self.env["generate.inv"]
            counter_product = 0.0

            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.ValidationError(_("Invalid file!"))
            values = {}

            for i in range(len(file_reader)):
                if i != 0:
                    val = {}
                    try:
                        field = list(map(str, file_reader[i]))
                    except ValueError:
                        raise exceptions.ValidationError(_("Dont Use Charecter only use numbers"))

                    values = dict(zip(keys, field))

                    if self.import_prod_option == "barcode":
                        prod_lst = product_obj.search([("barcode", "=", values["code"])])
                    elif self.import_prod_option == "code":
                        prod_lst = product_obj.search([("default_code", "=", values["code"])])
                    else:
                        prod_lst = product_obj.search([("name", "=", values["code"])])
                    if not values.get("location"):
                        raise ValidationError(_("Please fill 'LOCATION' column in CSV or XLS file."))
                    stock_location_id = self.env["stock.location"].search([("complete_name", "=", values["location"])])
                    if not stock_location_id:
                        raise ValidationError(_('"%s" Location is not available.') % (values["location"]))

                    if prod_lst:
                        val["product"] = prod_lst[0].id
                        val["quantity"] = values["quantity"]

                    if bool(val):
                        product_id = product_obj.browse(val["product"])
                        product_uom_obj = self.env["uom.uom"]
                        product_uom_id = product_uom_obj.search([("name", "=", values["uom"])])
                        if self.lot_option == True:
                            search_line = self.env["stock.quant"].search(
                                [
                                    ("product_id", "=", val["product"]),
                                    ("location_id", "=", stock_location_id.id),
                                    ("lot_id.name", "=", values["lot"]),
                                ]
                            )

                            if search_line:
                                for stock_line_id in search_line:
                                    stock_line_id.write({"inventory_quantity": val["quantity"]})
                                    stock_line_id.action_apply_inventory()

                            else:
                                stock_lot_obj = self.env["stock.production.lot"]
                                lot_id = stock_lot_obj.search(
                                    [("product_id", "=", val["product"]), ("name", "=", values["lot"])]
                                )
                                for lot in lot_id:
                                    lot_obj = stock_lot_obj.browse(lot_id)

                                if not lot_id:
                                    date_exp = self.make_inventory_date(values["date"])
                                    lot = stock_lot_obj.create(
                                        {
                                            "name": values["lot"],
                                            "product_id": val["product"],
                                            "expiration_date": date_exp,
                                            "company_id": self.env.user.company_id.id,
                                        }
                                    )
                                    lot_id = lot
                                if self.location_id_option == True:
                                    stock_line_id = inventory_obj.create(
                                        {
                                            "product_id": val["product"],
                                            "location_id": stock_location_id.id,
                                            "product_uom_id": product_uom_id.id,
                                            "inventory_quantity": val["quantity"],
                                            "lot_id": lot_id.id,
                                            "is_import": True,
                                        }
                                    )
                                else:
                                    stock_line_id = inventory_obj.create(
                                        {
                                            "product_id": val["product"],
                                            "product_uom_id": product_uom_id.id,
                                            "inventory_quantity": val["quantity"],
                                            "lot_id": lot_id.id,
                                            "is_import": True,
                                        }
                                    )
                                stock_line_id.action_apply_inventory()

                            flag = 1
                            for i in prod_lst:
                                counter_product += 1
                            g_inv_id = generate_inv.sudo().create({"product_counter_main": int(counter_product)})
                        else:
                            search_line = self.env["stock.quant"].search(
                                [("product_id", "=", val["product"]), ("location_id", "=", stock_location_id.id)]
                            )

                            if search_line:
                                for stock_line_id in search_line:
                                    stock_line_id.write({"inventory_quantity": val["quantity"]})
                                    stock_line_id.action_apply_inventory()

                            else:
                                if self.location_id_option == True:
                                    stock_line_id = inventory_obj.create(
                                        {
                                            "product_id": val["product"],
                                            "location_id": stock_location_id.id,
                                            "product_uom_id": product_uom_id.id,
                                            "inventory_quantity": val["quantity"],
                                            "is_import": True,
                                        }
                                    )
                                else:
                                    stock_line_id = inventory_obj.create(
                                        {
                                            "product_id": val["product"],
                                            "product_uom_id": product_uom_id.id,
                                            "inventory_quantity": val["quantity"],
                                            "is_import": True,
                                        }
                                    )

                                stock_line_id.action_apply_inventory()

                            flag = 1
                            for i in prod_lst:
                                counter_product += 1
                            g_inv_id = generate_inv.sudo().create({"product_counter_main": int(counter_product)})

                    else:
                        raise ValidationError(_('Product Not Found  "%s"') % values.get("code"))

            if flag == 1:
                return {
                    "name": _("Success"),
                    "view_type": "form",
                    "view_mode": "form",
                    "res_model": "generate.inv",
                    "view_id": self.env.ref("bi_generic_import.success_import_wizard").id,
                    "type": "ir.actions.act_window",
                    "target": "new",
                }
            else:
                return True

        else:

            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.ValidationError(_("Invalid file!"))
            product_obj = self.env["product.product"]

            inventory_obj = self.env["stock.quant"]

            flag = 0
            generate_inv = self.env["generate.inv"]
            counter_product = 0.0

            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row: row.value.encode("utf-8"), sheet.row(row_no))
                else:
                    line = list(
                        map(
                            lambda row: isinstance(row.value, bytes) and row.value.encode("utf-8") or str(row.value),
                            sheet.row(row_no),
                        )
                    )
                    if line:
                        if self.lot_option == True:
                            values.update(
                                {
                                    "line_location_id": line[0],
                                    "code": line[1],
                                    "quantity": line[2],
                                    "uom": line[3],
                                    "date": line[4],
                                    "lot": line[5],
                                }
                            )
                        else:
                            values.update(
                                {
                                    "line_location_id": line[0],
                                    "code": line[1],
                                    "quantity": line[2],
                                    "uom": line[3],
                                    "date": line[4],
                                }
                            )

                        if self.import_prod_option == "barcode":
                            prod_lst = product_obj.search([("barcode", "=", values["code"])])
                        elif self.import_prod_option == "code":
                            prod_lst = product_obj.search([("default_code", "=", values["code"])])
                        else:
                            prod_lst = product_obj.search([("name", "=", values["code"])])
                        stock_location_id = self.env["stock.location"].search(
                            [("complete_name", "=", values["line_location_id"])]
                        )
                        if not stock_location_id:
                            raise ValidationError(_('"%s" Location is not available.') % (values["line_location_id"]))

                        if prod_lst:
                            val["product"] = prod_lst[0].id
                            val["quantity"] = values["quantity"]
                        if bool(val):
                            product_id = product_obj.browse(val["product"])
                            product_uom_obj = self.env["uom.uom"]
                            product_uom_id = product_uom_obj.search([("name", "=", values["uom"])])
                            if self.lot_option == True:
                                search_line = self.env["stock.quant"].search(
                                    [
                                        ("product_id", "=", val["product"]),
                                        ("location_id", "=", stock_location_id.id),
                                        ("lot_id.name", "=", values["lot"]),
                                    ]
                                )

                                if search_line:
                                    for stock_line_id in search_line:
                                        stock_line_id.write({"inventory_quantity": val["quantity"]})
                                        stock_line_id.action_apply_inventory()

                                else:

                                    stock_lot_obj = self.env["stock.production.lot"]
                                    lot_id = stock_lot_obj.search(
                                        [("product_id", "=", val["product"]), ("name", "=", values["lot"])]
                                    )
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)

                                    if not lot_id:
                                        date_exp = self.make_inventory_date(values["date"])
                                        lot = stock_lot_obj.create(
                                            {
                                                "name": values["lot"],
                                                "product_id": val["product"],
                                                "expiration_date": date_exp,
                                                "company_id": self.env.user.company_id.id,
                                            }
                                        )
                                        lot_id = lot
                                    if self.location_id_option == True:
                                        stock_line_id = inventory_obj.create(
                                            {
                                                "product_id": val["product"],
                                                "location_id": stock_location_id.id,
                                                "product_uom_id": product_uom_id.id,
                                                "inventory_quantity": val["quantity"],
                                                "lot_id": lot_id.id,
                                                "is_import": True,
                                            }
                                        )
                                    else:
                                        stock_line_id = inventory_obj.create(
                                            {
                                                "product_id": val["product"],
                                                "product_uom_id": product_uom_id.id,
                                                "inventory_quantity": val["quantity"],
                                                "lot_id": lot_id.id,
                                                "is_import": True,
                                            }
                                        )

                                    stock_line_id.action_apply_inventory()

                                flag = 1
                                for i in prod_lst:
                                    counter_product += 1
                                g_inv_id = generate_inv.sudo().create({"product_counter_main": int(counter_product)})
                            else:
                                search_line = self.env["stock.quant"].search(
                                    [("product_id", "=", val["product"]), ("location_id", "=", stock_location_id.id)]
                                )

                                if search_line:
                                    for stock_line_id in search_line:
                                        stock_line_id.write({"inventory_quantity": val["quantity"]})
                                        stock_line_id._compute_inventory_diff_quantity()
                                        if self.is_validate_inventory == True:
                                            stock_line_id.action_apply_inventory()

                                else:
                                    if self.location_id_option == True:
                                        stock_line_id = inventory_obj.create(
                                            {
                                                "product_id": val["product"],
                                                "location_id": stock_location_id.id,
                                                "product_uom_id": product_uom_id.id,
                                                "inventory_quantity": val["quantity"],
                                                "is_import": True,
                                            }
                                        )
                                    else:
                                        stock_line_id = inventory_obj.create(
                                            {
                                                "product_id": val["product"],
                                                "product_uom_id": product_uom_id.id,
                                                "inventory_quantity": val["quantity"],
                                                "is_import": True,
                                            }
                                        )

                                    stock_line_id.action_apply_inventory()

                                flag = 1
                                for i in prod_lst:
                                    counter_product += 1
                                g_inv_id = generate_inv.sudo().create({"product_counter_main": int(counter_product)})
                        else:
                            raise ValidationError(_('Product Not Found  "%s"') % values.get("code"))

            if flag == 1:
                return {
                    "name": _("Success"),
                    "view_type": "form",
                    "view_mode": "form",
                    "res_model": "generate.inv",
                    "view_id": self.env.ref("bi_generic_import.success_import_wizard").id,
                    "type": "ir.actions.act_window",
                    "target": "new",
                }
            else:
                return True


class StockQuant(models.Model):
    _inherit = "stock.quant"

    is_import = fields.Boolean(string=" Is Imported data", default=False)

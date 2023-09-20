from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ref_number = fields.Char(string="Ref. Number")

    @api.model
    def create(self, vals):

        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        vals["ref_number"] = self.env["ir.sequence"].next_by_code(
            "lbc.ref.number", sequence_date=seq_date
        )
        return super(ResPartner, self).create(vals)

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "%s %s" % (record.name, (record.ref_number or "")))
            )

        return result

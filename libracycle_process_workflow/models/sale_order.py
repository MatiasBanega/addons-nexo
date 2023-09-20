from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    name = fields.Char(
        string="Invoice Number",
        required=True,
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        index=True,
    )

    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account',  required=False)

    @api.model
    def create(self, vals):
        name = vals.get("name")
        if not name:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "lbc.invoice.number", sequence_date=seq_date
            )
        return super(SaleOrder, self).create(vals)

    @api.onchange("analytic_account_id")
    def _onchange_analytic_account_id(self):
        for rec in self:
            project_ids = rec.analytic_account_id.project_ids
            print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@', project_ids)
            if project_ids:
                rec.project_id = project_ids[0].id

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update(bank_account_id=self.bank_account_id)
        return invoice_vals

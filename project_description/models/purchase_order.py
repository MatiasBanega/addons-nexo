from odoo import models, api, fields


class StockPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _default_job_id(self):
        job_id = False
        if self._context.get("job_id") or self._context.get("default_job_id"):
            job_id = self._context.get("job_id") or self._context.get("default_job_id")
        return job_id

    job_id = fields.Many2one("project.project", string="Job ID", default=_default_job_id)


class StockPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.onchange("product_id")
    def onchange_product_id(self):
        res = super(StockPurchaseOrderLine, self).onchange_product_id()
        if self._context.get("analytic_account_id") or self.order_id.job_id:
            self.account_analytic_id = self._context.get(
                "analytic_account_id", self.order_id.job_id.analytic_account_id.id
            )
        return res

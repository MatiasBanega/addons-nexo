from datetime import datetime
from odoo import models, fields, api, _


class IRRequestApprove(models.Model):
    _name = "ng.ir.request.approve"
    _description = "ng.ir.request.approve"

    STATE = [
        ("not_available", "Not Available"),
        ("partially_available", "Partially Available"),
        ("available", "Available"),
        ("awaiting", "Awaiting Availability"),
    ]

    request_id = fields.Many2one(comodel_name="ng.ir.request", string="Request")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    quantity = fields.Float(string="Quantity", default=1.0)
    uom = fields.Many2one(comodel_name="uom.uom", string="UOM", related="product_id.uom_id", store=True)
    qty = fields.Float(string="Qty Available", compute="_compute_quantity_available")
    state = fields.Selection(selection=STATE, string="State", compute="_compute_state", store=False)
    purchase_agreement_id = fields.Many2one(
        comodel_name="purchase.requisition", string="Purchase Agreement", readonly=True
    )
    to_procure = fields.Boolean(string="To Procure", compute="_compute_to_procure")
    transferred = fields.Boolean(string="Transferred", default=False)
    button_show_state = fields.Boolean(string="Show State", compute="_compute_button_show_state")

    @api.depends("product_id", "request_id.state")
    def _compute_button_show_state(self):
        for rec in self:
            rec.button_show_state = rec.request_id.state == "approval1"

    @api.depends("state")
    def _compute_to_procure(self):
        for rec in self:
            to_procure = rec.state == "partially_available" or rec.state == "not_available"
            if rec.purchase_agreement_id:
                rec.to_procure = False
            else:
                rec.to_procure = to_procure

    @api.depends("product_id")
    def _compute_quantity_available(self):
        for rec in self:
            location_id = rec.request_id.src_location_id.id
            product_id = rec.product_id.id
            domain = [("location_id", "=", location_id), ("product_id", "=", product_id)]
            stock_quants = self.env["stock.quant"].search(domain)
            rec.qty = sum([stock_quant.quantity for stock_quant in stock_quants])

    @api.depends("qty")
    def _compute_state(self):
        for rec in self:
            if rec.qty <= 0:
                rec.state = "not_available"
            elif rec.qty > 0 and rec.qty < rec.quantity:
                rec.state = "partially_available"
            else:
                rec.state = "available"

    def procure(self):
        product_id, quantity = self.product_id, self.quantity - self.qty
        requisition = self.env["purchase.requisition"]
        line = self.env["purchase.requisition.line"]
        request_identity = self.request_id.name
        requisition_id = requisition.create({"name": ""})
        payload = {
            "product_id": product_id.id,
            "product_uom_id": product_id.uom_id.id,
            "product_qty": quantity,
            "qty_ordered": quantity,
            "requisition_id": requisition_id.id,
            "price_unit": product_id.standard_price,
        }
        line.create(payload)
        self.purchase_agreement_id = requisition_id.id
        # Rename the purchase requestion name to ref
        origin = "{}".format(request_identity,)
        requisition_id.write({"name": origin})

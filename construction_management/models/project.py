# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp


class project_project(models.Model):
    _inherit = 'project.project'

    def _find_cost(self):
        bill_qty_obj = self.env['bill.quantity'].search([])
        bill_qty_search = bill_qty_obj.filtered(lambda s: s.project_id.id == self.id)
        count = 0
        pro_cost = 0.0
        for record in bill_qty_search:
            count = 1
            pro_cost += (record.material_cost + record.labor_cost + record.subcontract_cost + record.work_package_cost)
        self.update({'project_cost' : pro_cost,})
        return True

    def _find_line_usage(self):
        bill_qty_line_obj = self.env['bill.quantity.line']
        count = 0
        flag = 0
        bill_qty_line_search = bill_qty_line_obj.search([])
        for line in bill_qty_line_search:
            if line.bill_quantity_id.project_id.id == self.id:
                if line.key == 'material' and line.product_id:
                    vals = {
                        'product_id': line.product_id.id,
                        'uom_id': line.uom_id.id,
                        'qty': line.qty,
                        'price_unit': line.price_unit,
                        'price_subtotal': line.price_subtotal,
                        'project_id': line.bill_quantity_id.project_id.id
                    }
                    count = 1
                    self.inventory_usages_ids |= self.env['product.product.extension'].create(vals)
                if line.key == 'work_package' and line.work_package_id:
                    vals = {
                        'work_package_id': line.work_package_id.id,
                        'uom_id': line.uom_id.id,
                        'qty': line.qty,
                        'price_unit': line.price_unit,
                        'price_subtotal': line.price_subtotal,
                        'project_id': line.bill_quantity_id.project_id.id
                    }
                    flag = 1
                    self.work_package_ids |= self.env['work.package.extension'].create(vals)
        if count == 0:
            self.inventory_usages_ids = False
        if flag == 0:
            self.work_package_ids = False
        # return True

    sale_order_ids = fields.Many2many("sale.order", string="Sale Order Reference")
    purchase_order_ids = fields.Many2many("purchase.order", string="Purchase Order Reference")
    work_package_ids = fields.One2many("work.package.extension", 'project_id', string="Work Package Reference",
                                       compute="_find_line_usage")
    inventory_usages_ids = fields.One2many("product.product.extension", 'project_id',
                                           string="Inventory Usage Reference", compute="_find_line_usage")
    project_deliverables_ids = fields.One2many('material.line', 'project_id', string='Deliverable')
    project_cost = fields.Float(string="Project Cost", compute="_find_cost",default = 0.0)


class material_line(models.Model):
    _name = "material.line"
    _description = 'Material Line'

    project_id = fields.Many2one('project.project', 'Material')
    product_id = fields.Many2one('product.product', 'Products')
    planned_qty = fields.Integer('Planned Qty.')
    used_qty = fields.Float('Used Qty')
    status = fields.Selection([('close', 'Close'), ('open', 'Open')], "State", default="open")


class work_package_extension(models.Model):
    _name = 'work.package.extension'
    _description = 'Work Package Extension'

    project_id = fields.Many2one('project.project', 'Project')
    work_package_id = fields.Many2one('work.package', 'Work Package')
    uom_id = fields.Many2one('uom.uom', 'Product UOM')
    qty = fields.Float('QTY', default =0.0)
    price_unit = fields.Float('Price Unit', default =0.0)
    price_subtotal = fields.Float('Price Subtotal', default =0.0)


class project_deliverables(models.Model):
    _name = 'project.deliverables'
    _description = 'Project Deliverables'
    project_id = fields.Many2one('project.project', 'Project')


class product_product_extension(models.Model):
    _name = 'product.product.extension'
    _description = 'Product Product Extension'

    project_id = fields.Many2one('project.project', 'Project')
    product_id = fields.Many2one('product.product', 'Product')
    uom_id = fields.Many2one('uom.uom', 'Product UOM')
    qty = fields.Float('QTY', default =0.0)
    price_unit = fields.Float('Price Unit' , default =0.0)
    price_subtotal = fields.Float('Price Subtotal' , default =0.0)

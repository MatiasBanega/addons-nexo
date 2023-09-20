# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta


class note_note(models.Model):
    _inherit = 'note.note'

    construction_proj_id = fields.Many2one('project.project', 'Construction Project')
    responsible_user = fields.Many2one('res.users', 'Responsible Person')
    task_id = fields.Many2one('project.task', 'Project Task')


class material_details(models.Model):
    _name = 'material.details'
    _description = 'Material Details'

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.name = self.product_id.name
        self.uom_id = self.product_id.uom_id

    product_id = fields.Many2one('product.product', 'Product')
    name = fields.Char('Description')
    product_qty = fields.Float('Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    task_id = fields.Many2one('project.task', 'Task')


class material_consume(models.Model):
    _name = 'material.consume'
    _description = 'Material Consume'

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.name = self.product_id.name
        self.uom_id = self.product_id.uom_id

    product_id = fields.Many2one('product.product', 'Product')
    name = fields.Char('Description')
    product_qty = fields.Float('Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    task_id = fields.Many2one('project.task', 'Task')


class product_product(models.Model):
    _inherit = 'product.product'

    boq_type = fields.Selection([('machine_qui', 'Machinery / Equipment'), ('worker', 'Worker / Resource'),
                                 ('work_package', 'Work Cost Package'), ('subcontract', 'Subcontract')], 'BOQ Type')
    project_task_id = fields.Many2one('project.task', string='Project Task')

class project_task(models.Model):
    _inherit = 'project.task'

    prod_material_ids = fields.One2many('material.details', 'task_id')
    consume_material_ids = fields.One2many('material.consume', 'task_id')
    material_req_stock_ids = fields.One2many('stock.picking', 'job_orders_id')
    stock_move_ids = fields.One2many('stock.move', 'project_stock_move_id')


class stock_move(models.Model):
    _inherit = 'stock.move'

    project_stock_move_id = fields.Many2one('project.task', string='Stock Move')


class product_template(models.Model):
    _inherit = 'product.template'

    pur_order_wiz_id = fields.Many2one('purchase.order.wizard', string='Ordersss')


class res_partner(models.Model):
    _inherit = 'res.partner'

    res_partner_id = fields.Many2one('purchase.order.wizard', string='partner')


class product_template(models.Model):
    _inherit = 'product.product'

    quantity = fields.Integer(string="Quantity")
    tmpl_id = fields.Many2one('purchase.order.wizard', string='Products')


class product_purchase_order(models.Model):
    _name = 'product.purchase.order'
    _description = 'Product Purchase Order'

    pro_ids = fields.Many2one('product.product', 'Products')
    pro_pur_ids = fields.Many2one('purchase.order.wizard', 'Product')
    quantity = fields.Float('Quantity', default=1.0)
    on_hand_qty = fields.Float('On Hand Quantity')


class purchase_order_wizard(models.Model):
    _name = 'purchase.order.wizard'
    _description = 'Purchase Order Wizard'

    partner_ids = fields.Many2many('res.partner', 'wizard_partner_rel', 'purchase_partner_id', 'purchase_line_id',
                                   string='Partner')
    product_ids = fields.Many2many('product.product', 'wizard_product_rel', 'purchase_product_id',
                                   'purchase_product_line_id', string='Products')
    pur_pro_id = fields.One2many('product.purchase.order', 'pro_pur_ids', readonly=True)

    @api.model
    def default_get(self, values):
        list_of_order = []
        result = super(purchase_order_wizard, self).default_get(values)
        stock_picking = self.env['stock.picking'].browse(self._context.get('active_id'))

        for pro_ids in stock_picking.move_lines:
            quant = self._cr.execute('select "id" from "stock_quant" WHERE product_id = %s order by "id"',
                                     (pro_ids.product_id.id,))
            id_returned = self._cr.fetchone()
            if id_returned:
                stock_quant = self.env['stock.quant'].browse(id_returned)

                list_of_order += [(0, 0, {
                    'pro_ids': pro_ids.product_id.id,
                    'quantity': pro_ids.product_uom_qty,
                    'on_hand_qty': stock_quant.quantity,
                })]
                result.update({
                    'pur_pro_id': list_of_order,
                })
            else:
                stock_quant = self.env['stock.quant'].browse(id_returned)

                list_of_order += [(0, 0, {
                    'pro_ids': pro_ids.product_id.id,
                    'quantity': pro_ids.product_uom_qty,
                    'on_hand_qty': stock_quant.quantity,
                })]
                result.update({
                    'pur_pro_id': list_of_order,
                })
        return result

    def create_purchase_order(self):
        stock_picking_id = self.env['stock.picking'].browse(self._context.get('active_id'))
        vals = {}
        list_of_order = []
        for par_id in self.partner_ids:
            vals['partner_id'] = par_id.id
            vals['date_order'] = datetime.now()

            purchase_order = self.env['purchase.order'].create(vals)
            vals = {}
            list_of_order.append(purchase_order)

            for products in self.pur_pro_id:
                vals['product_id'] = products.pro_ids.id
                vals['product_qty'] = products.quantity
                vals['name'] = products.pro_ids.name
                vals['price_unit'] = products.pro_ids.list_price
                vals['date_planned'] = datetime.now()
                vals['order_id'] = purchase_order.id
                vals['product_uom'] = products.pro_ids.uom_id.id
                purchase_order_line = self.env['purchase.order.line'].create(vals)
            vals = {}
        return True


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    job_orders_id = fields.Many2one('project.task', 'Task / Job Orders')
    job_orders_user_ids = fields.Many2many('res.users',relation='stock_pick_user_rel',string='Task / Job Orders User')
    construnction_pro_id = fields.Many2one('project.project', 'Construction Project')
    analylic_acc_id = fields.Many2one('account.analytic.account', 'Analylic Account')
    bill_of_qty_id = fields.Many2one('bill.quantity', 'Bill Of Quantity')
    cost_equipment = fields.Float(string="Equipment Cost")
    worker_cost = fields.Float(related='bill_of_qty_id.labor_cost', string="Worker / Resource Cost", store=True)
    work_cost_package = fields.Float(related='bill_of_qty_id.work_package_cost', string="Work Cost Package", store=True)
    sub_contract_cost = fields.Float(related='bill_of_qty_id.subcontract_cost', string="SubContract Cost", store=True)
    project_task_stock_id = fields.Many2one('project.task', string='Project Task')

    @api.onchange('job_orders_id')
    def _onchange_job_orders_id(self):
        self.job_orders_user_ids = self.job_orders_id.user_ids
        self.construnction_pro_id = self.job_orders_id.project_id

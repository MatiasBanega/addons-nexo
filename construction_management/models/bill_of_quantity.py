# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp


class bill_quantity(models.Model):
    _name = 'bill.quantity'
    _description = 'Bill Quantity'
    _inherit = ['mail.thread']
    _rec_name = 'project_id'

    @api.depends('quantity_line.qty','quantity_line.price_unit')
    def _compute_amount(self):
        material_price_subtotal = 0.0
        labor_price_subtotal = 0.0
        subcontract_price_subtotal = 0.0
        equipment_price_subtotal = 0.0
        work_package_price_subtotal = 0.0
        for i in self:
            if i.quantity_line:
                for record in i.quantity_line:
                    if record.key == 'material':
                        material_price_subtotal += record.price_subtotal
                    if record.key == 'labor':
                        labor_price_subtotal += record.price_subtotal
                    if record.key == 'subcontract':
                        subcontract_price_subtotal += record.price_subtotal
                    if record.key == 'work_package':
                        work_package_price_subtotal += record.price_subtotal
                        
            i.update({'subcontract_cost' :subcontract_price_subtotal,
                        'labor_cost' : labor_price_subtotal,
                        'work_package_cost':work_package_price_subtotal,
                        'material_cost': material_price_subtotal,})


    project_id = fields.Many2one(
        'project.project', 'Project', tracking=True)
    revision = fields.Integer(
        'Revision', readonly=True)
    parent_id = fields.Many2one('bill.quantity');
    subcontract_cost = fields.Float(
        'Subcontract Cost',default = 0.0,  
        store=True,digits='Account',compute="_compute_amount")
    material_cost = fields.Float(
        'Material Cost',
        store=True, default = 0.0,
        digits='Account', compute="_compute_amount")
    labor_cost = fields.Float(
        'Labor Cost',
        store=True, default = 0.0,
        digits='Account', compute="_compute_amount")
    work_package_cost = fields.Float(
        'Work Package Cost',
        store=True,default = 0.0,
        digits='Account', compute="_compute_amount")
    quantity_line = fields.One2many(
        'bill.quantity.line', 'bill_quantity_id',
        string='Bill Of Quantity Lines', readonly=False, copy=True)

    def create_new_revision(self):
        bill_line = []
        for line in self.quantity_line:
            bill_line.append(
                (0, False, {'product_id': line.product_id.id,
                            'type': line.type,
                            'uom_id': line.uom_id.id,
                            'description': line.description,
                            'qty': line.qty,
                            'bill_quantity_id': self.id,
                            'key': line.key,
                            'employee_id': line.employee_id.id,
                            'product_id': line.product_id.id,
                            'partner_id': line.partner_id.id,
                            'work_package_id': line.work_package_id.id,
                            'price_unit': line.price_unit,
                            'price_subtotal': line.price_subtotal,
                            }))
        vals = {'project_id': self.project_id.id,
                'quantity_line': bill_line,
                'parent_id': self.parent_id.id if self.parent_id else self.id,
                }
        res = self.create(vals)
        res.revision =  self.total_revisions(res.parent_id)

    def total_revisions(self,parent_id):
        ids = self.env["bill.quantity"].search([]);
        ids = ids.filtered(lambda s: s.parent_id.id == parent_id.id);
        maxx = 0;
        if ids:
            for rec in ids:
                if rec.revision > maxx:
                    maxx = rec.revision;
        else:
            return self.revision + 1;
        return maxx + 1;


class bill_quantity_line(models.Model):
    _name = 'bill.quantity.line'
    _description = 'Bill Of Quantity Line'

    @api.depends('price_unit', 'qty', 'product_id')
    def _compute_price(self):
        for i in self:
            i.price_subtotal = i.qty * i.price_unit

    bill_quantity_id = fields.Many2one(
        'bill.quantity', string='Bill of Quantity Reference',
        ondelete='cascade', index=True)
    key = fields.Selection(
        [
            ('labor', 'Labor'),
            ('material', 'Material'),
            ('subcontract', 'Subcontract'),
            ('work_package', 'Work Package'),
        ], 'Key', default='labor')
    product_id = fields.Many2one(
        'product.product', string='Product',
        ondelete='restrict', index=True)
    employee_id = fields.Many2one(
        'hr.employee', 'Employee', )
    partner_id = fields.Many2one(
        'res.partner', string='Partners', )
    work_package_id = fields.Many2one(
        'work.package', string='Work Package', )
    type = fields.Char('Type', size=64, )
    description = fields.Char(
        'Description', size=64, )
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', )
    qty = fields.Float("Qty", default=1)
    price_unit = fields.Float(
        "Rate", digits='Account',default = 0.0, )
    price_subtotal = fields.Float(
        "Total", compute='_compute_price',default = 0.0,
        readonly=True, store=True,
        digits='Account', )

    @api.onchange("work_package_id")
    def _onchange_key(self):
        for rec in self:
            if rec.key == "work_package":
                if rec.work_package_id:
                    rec.price_unit = rec.work_package_id.work_package_cost;

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

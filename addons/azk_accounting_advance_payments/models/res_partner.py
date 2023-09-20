from odoo import fields, models
import logging

log = logging.getLogger(__name__)

class Company(models.Model):
    _inherit = 'res.partner'
    
    prepayment_payable_id = fields.Many2one('account.account', company_dependent=True,
        string="Prepayment Account Payable",
        domain="[('deprecated', '=', False)]",
        help="This account will be used for advance payment as the payable account for the current partner",)
    prepayment_receivable_id = fields.Many2one('account.account', company_dependent=True,
        string="Prepayment Account Receivable",
        domain="[('deprecated', '=', False)]",
        help="This account will be used for advance payment as the receivable account for the current partner",)
    prepayment_vat_receivable_id = fields.Many2one('account.account', company_dependent=True,
        string="Prepayment VAT Receivable Account",
        domain="[('deprecated', '=', False)]",
        help="This account will be used for advance payment as the VAT receivable account for the current partner",)
    prepayment_vat_payable_id = fields.Many2one('account.account', company_dependent=True,
        string="Prepayment VAT Payable Account",
        domain="[('deprecated', '=', False)]",
        help="This account will be used for advance payment as the VAT payable account for the current partner",)

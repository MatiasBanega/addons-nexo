from odoo import models


class ProductPriceListItem(models.Model):
    _inherit = "sale.order.line"
   
    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        result = super()._get_real_price_currency(product, rule_id, qty, uom, pricelist_id)
        
        pricelist_item = self.env['product.pricelist.item'].browse(rule_id)
        if rule_id and pricelist_item.base == 'designation_cost' and product.use_designation_cost :
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    _price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

                product_currency = product.cost_currency_id
                currency_id = pricelist_item.pricelist_id.currency_id
    
                if not currency_id:
                    currency_id = product_currency
                    cur_factor = 1.0
                else:
                    if currency_id.id == product_currency.id:
                        cur_factor = 1.0
                    else:
                        cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.company, self.order_id.date_order or fields.Date.today())
        
                product_uom = self.env.context.get('uom') or product.uom_id.id
                if uom and uom.id != product_uom:
                    uom_factor = uom._compute_price(1.0, product.uom_id)
                else:
                    uom_factor = 1.0
                    
                result = product.designation_cost * uom_factor * cur_factor, currency_id

        return result
   
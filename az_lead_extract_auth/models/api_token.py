from odoo import models, fields, api, _
from datetime import datetime, timedelta
import string
import secrets
import logging

log = logging.getLogger(__name__)



class ApiAccessToken(models.Model):
    _name = "az.api.access.token"
    _description = "User Access Token"
    
    
    user_id = fields.Many2one('res.users', string='User', help="Token User")
    api_token = fields.Char('Api Access Token', help='Token to be used for user authentication')
    expiry_date = fields.Datetime('Expiry Date', help='Token Expiry Date')
    last_accessed = fields.Datetime('Last Accessed', help='Token Last Accessed')
    
    def generate_token(self, length=40):
        """
            Generate hashed token and return specific length of it
        """

        return secrets.token_urlsafe(40)
    
    
    def create_token(self, user):
        """
            Create token for user, set expiration date
        """
        
        token_expiration = self.env['ir.config_parameter'].sudo().get_param('az_lead_extract_auth.api_token_expiration') or 0
        
        access_token = self.generate_token()
        token_exp_date = datetime.now() + timedelta(minutes=int(token_expiration)) if token_expiration != 0 else False
        
        return self.create({
                       'user_id': user.id,
                       'api_token': access_token,
                       'expiry_date':  token_exp_date
                       })
        
    def check_access_token(self, token):
        """
            check access token existance and validity
        """
        msg = ''
        token = self.sudo().search([('api_token', '=', token)], order='expiry_date desc', limit=1)
        
        if not token:
            token = False
            msg = _('Invalid token')
        elif token.expiry_date and token.expiry_date < datetime.now():
            token = False
            msg = _('Token Expired')
            
        return token, msg
        
    def update_token_last_accessed(self):
        self.write({'last_accessed': datetime.now()})
        
        
    def cron_delete_expired_tokens(self):
        tokens = self.env['az.api.access.token'].sudo().search([('expiry_date', '!=', False), ('expiry_date', '<', datetime.now())]).unlink()
        
    
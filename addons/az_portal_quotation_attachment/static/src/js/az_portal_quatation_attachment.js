odoo.define('az_portal_so.quatation_attachment', function (require) {
    'use strict';

    var core = require('web.core');
	var QWeb = core.qweb;
	var qweb = core.qweb;
	var SignatureFormDict = require('portal.signature_form');
	var rpc = require('web.rpc');
	var session = require('web.session');
	
	
	 SignatureFormDict.SignatureForm.include({
		 template: 'az_portal_quotation_attachment.portal_signature', 
		 xmlDependencies: [ '/az_portal_quotation_attachment/static/src/xml/portal_signature_inherited.xml'],
		events: {
	        'click .o_portal_sign_submit': 'async _onClickSignSubmit',
			'click .o_portal_sign_upload': 'async _OnSignUpload',
			'click .o_portal_sign_upload_cancel': 'async _OnSignUploadCancel',
	    },
		

		_OnSignUpload : function(ev){
			let $file = $('.az_purchase_file');
			let $uploadBtn = $('.o_portal_sign_upload');
			let $cancelBtn = $('.o_portal_sign_upload_cancel');
			
			$file.css('display', 'inline-block');
			$uploadBtn.css('display', 'none');
			$cancelBtn.css('display', 'inline-block');
			$file.trigger('click');
		},
		
		_OnSignUploadCancel(evt){
			let $file = $('.az_purchase_file');
			let $uploadBtn = $('.o_portal_sign_upload');
			let $cancelBtn = $('.o_portal_sign_upload_cancel');
			
			$uploadBtn.css('display', 'inline-block');
			$cancelBtn.css('display', 'none');
			$file.val('');
			$file.css('display', 'none');
		},
		
		_onClickSignSubmit: function (ev) {
			
	       var self = this;
	        ev.preventDefault();
	
	        if (!this.nameAndSignature.validateSignature()) {
	            return;
	        }
	
	        var name = this.nameAndSignature.getName();
	        var signature = this.nameAndSignature.getSignatureImage()[1];
			
	        return this._rpc({
	            route: this.callUrl,
	            params: _.extend(this.rpcParams, {
	                'name': name,
	                'signature': signature,
	            }),
	        }).then(function (data) {
	            if (data.error) {
	                self.$('.o_portal_sign_error_msg').remove();
	                self.$controls.prepend(qweb.render('portal.portal_signature_error', {widget: data}));
	            } else if (data.success) {
					self._sendPoFile();
	                var $success = qweb.render('portal.portal_signature_success', {widget: data});
	                self.$el.empty().append($success);
	            }
	            if (data.force_refresh) {
					self._sendPoFile();
	                if (data.redirect_url) {
	                    window.location = data.redirect_url;
	                } else {
	                    window.location.reload();
	                }
	                // no resolve if we reload the page
	                return new Promise(function () { });
	            }
	        });
	    },
		
		_sendPoFile(){
			var self = this;
			var formData = new FormData();
			var $file = $('.az_purchase_file');
			var $csrf =  $('input[name="csrf_token"]')
			var po_file = false;
			if($file[0].files.length > 0){
				 po_file =  $file[0].files[0];
				formData.append('purchase_file', po_file, po_file.name);
				formData.append('csrf_token', $csrf.val());
				var callUrl = self.callUrl
				var url = callUrl.substring(0,  callUrl.indexOf('?')) + "/upload_attachment" + callUrl.substring(callUrl.indexOf('?'));
				
				$.ajax({
					    url: url,
						type: 'POST',
						async:false, 
						data: formData,
						processData: false,
						contentType: false,
						xhr: function () {
								return new XMLHttpRequest();
							},
					  }).done(function(data) {
						
					  }).fail(function() {
				    	bootbox.alert("Could not upload attachment");
				  	});
			}
		}
		
	});
	
	var orig_sig_start_fn =  SignatureFormDict.SignatureForm.prototype.start;
	SignatureFormDict.SignatureForm.prototype.start =  function () {
		var result = orig_sig_start_fn.call(this);
		 rpc.query({model: 'res.company', method: 'read', args: [[session.website_company_id]]})
                .then(function (backend_result) {
                  
                    return Promise.resolve(
							 $('#az_po_upload_warning').text(backend_result[0].portal_sale_attachemnt_warning ||
						" In case the purchase order is not available, the confirmation will get the job moving. However, No delivery will be made unless the purchase order is obtained.")
						);
                });

		return result;
	};
	
	return SignatureFormDict
	
})

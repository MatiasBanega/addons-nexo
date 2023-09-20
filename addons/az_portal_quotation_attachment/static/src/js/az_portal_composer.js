odoo.define('az_portal_so.composer', function (require) {
    'use strict';

    var core = require('web.core');
	var QWeb = core.qweb;
	var composer = require('portal.composer');
	var rpc = require('web.rpc');
	
	var orig_start_fn = composer.PortalComposer.prototype.start;
	
 	composer.PortalComposer.prototype.start =  function () {
		
		if(this.options.res_model =='sale.order'){
			 rpc.query({model: 'sale.order', method: 'read', args: [[this.options.res_id]]})
                .then(function (backend_result) {

                   if(backend_result && backend_result[0].state == 'sent'){
						$('.o_portal_chatter_attachment_btn').text( 'Attach Purchase Order');

					}
                    return Promise.resolve();
                });
			
		}
		var result = orig_start_fn.call(this);
		
		return result;
	};

	return composer;
	
})

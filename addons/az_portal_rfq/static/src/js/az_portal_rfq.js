odoo.define('az_portal_rfq.vendor_fill_prices', function (require) {
    'use strict';

    require('web.dom_ready')
	
	initPriceButton();
	initSubmitButton();
	initUpdatePrice();
	initIsnumber();

	function initPriceButton(){
	 	let btn_my_prices= ".azPriceBtn"
		let $btn_my_prices = $(btn_my_prices)
		$btn_my_prices .click(function(){
			let line_id =  this.getAttribute('data-line_id');
			$('#order_line_id').val(line_id);
			$("#rfqPortalModal").modal("show");
		})
	}

    function initUpdatePrice(){
		$('#update_rfq_prices').click(function(){
			let $date = $('#rfq_date');
			let $price = $('#rfq_unit_price');
			
			if($date.val() == ''){
				bootbox.alert('date is required');
				return false;
			}
			if($price.val() == ''){
				bootbox.alert('price is required');
				return false;
			} 
			
			$.ajax({
			    url: "/azk_rfq/portal/save_rfq_price",
				type: 'POST',
				async:false, 
				data: $("#frmMyPrices").serialize(),
				beforeSend: function() {
		       		 $('#loader').removeClass('hidden')
		    	 },
				  }).done(function(data) {
					$("#rfqPortalModal").modal("hide");
					$(".o_portal_sidebar").html(data);
					initPriceButton();
					initSubmitButton();
					initUpdatePrice();
					initIsnumber();
					$("#frmMyPrices").trigger('reset');
					$('#loader').addClass('hidden');
					
				  }).fail(function() {
				    console.log("unable to add record");
					bootbox.alert("unable to add data");
					$('#loader').addClass('hidden');
			    
			  });
		});
	
	}
	
	function initSubmitButton(){
		 $('#azSubmitPriceBtn').click(function(){
			let order_id =  this.getAttribute('data-order_id');
	
			$.ajax({
			    url: "/azk_rfq/portal/submit_rfq_price",
				type: 'POST',
				async:false,
				data: {'order_id': order_id},
				beforeSend: function() {
		       		 $('#loader').removeClass('hidden')
		    	 },
				
				  }).done(function(data) {
					$(".o_portal_sidebar").html(data);
					$('#loader').addClass('hidden');
					
				  }).fail(function() {
				    console.log("unable to submit data");
					bootbox.alert("unable to submit data");
					$('#loader').addClass('hidden');
			    
			  });
		});
	}
	
	function initIsnumber(){
		$('#rfq_unit_price').keypress(function(evt){
			 var charCode = (evt.which) ? evt.which : evt.keyCode;
		      if (charCode == 46) {
		        //Check if the text already contains the . character
		        if (this.value.indexOf('.') === -1) {
		          return true;
		        } else {
		          return false;
		        }
		      } else {
		        if (charCode > 31 && (charCode < 48 || charCode > 57))
		          return false;
		      }
		      return true;
		});
	}
	
	
	
})

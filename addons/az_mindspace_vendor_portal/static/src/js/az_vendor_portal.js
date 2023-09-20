odoo.define('az_portal_rfq.vendor_portal', function (require) {
    'use strict';

    require('web.dom_ready')
	
	initPriceButton();
	initSubmitButton();
	initUpdatePrice();
	initDeclineButton();
	initSubmitDecline();
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
	
	function initDeclineButton(){
		let $btn_decline = $('#azDeclineBtn')
		$btn_decline .click(function(){
			let order_id =  this.getAttribute('data-order_id');
			$('#decline_order_line_id').val(order_id);
			$("#rfqDeclineModal").modal("show");
		})
	}


    function initUpdatePrice(){
		$('#update_rfq_prices').click(function(){
			let $date = $('#rfq_date');
			let $price = $('#rfq_unit_price');
			
			/*if($date.val() == ''){
				bootbox.alert('date is required');
				return false;
			}*/
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
					initDeclineButton();
					initSubmitDecline();
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
	
	$('#chk_rfq_terms').change(function(){
		if(this.checked)
			$('#rfq_terms_content').css('background-color', '');
			
	})
	
	function initSubmitButton(){
		 $('#azSubmitPriceBtn').click(function(){
			let order_id =  this.getAttribute('data-order_id');
			let $terms_approved = $('#chk_rfq_terms')
			let $submitted_by = $('#rfq_submitted_by')
			
			if($terms_approved.prop('checked') == false){
				bootbox.alert("You must agree to our Terms & Conditions");
				$('#rfq_terms_content').css('background-color', '#f44336');
				return false;
			}else{
				$('#rfq_terms_content').css('background-color', '');
			}
			
			if($submitted_by.val() == ''){
				bootbox.alert("You must enter your name");
				$submitted_by.css('background-color', '#f44336');
				return false;
			}else{
				$submitted_by.css('background-color', '');
			}
			$.ajax({
			    url: "/azk_rfq/portal/submit_rfq_price",
				type: 'POST',
				async:false,
				data: {'order_id': order_id, 'submitted_by': $submitted_by.val()},
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
	
	function initSubmitDecline(){
		$('#submit_decline').click(function(){
			let $reason = $('#po_decline_reson');
			
			if($reason.val() == ''){
				bootbox.alert('Decline Reason is required');
				return false;
			} 
			
			$.ajax({
			    url: "/azk_rfq/portal/decline",
				type: 'POST',
				async:false, 
				data: $("#frmPoDeclineReason").serialize(),
				beforeSend: function() {
		       		 $('#loader').removeClass('hidden')
		    	 },
				  }).done(function(data) {
						data = JSON.parse(data)
						if(data.status == 'fail'){
							bootbox.alert(data.msg);
							$('#loader').addClass('hidden');
						}						
						else
						 	location.reload();
					
				  }).fail(function() {
				    console.log("unable to add record");
					bootbox.alert("unable to add data");
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

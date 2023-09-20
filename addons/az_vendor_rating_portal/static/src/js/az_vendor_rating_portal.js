odoo.define('az_vendor_rating_portal.vendor_rating', function (require) {
    'use strict';

    require('web.dom_ready')
	
	 


	$(function () {
	    var ctx = document.getElementById("vendorRatingChart").getContext("2d");
	    // examine example_data.json for expected response data
	  	var barColors = [
			 "#b91d47",
			 "#00aba9",
			 "#2b5797",
			"#0E6655",
			"#A93226",
			 "#e8c3b9",
			 "#1e7145",
			 
		];
	    // draw empty chart
	    var myChart = new Chart(ctx, {
	        type: 'bar',
	        data: {
	            labels: [],
	            datasets: [
	                {
	                    label: "Vendor Rating",
	                    fill: false,
	                    lineTension: 0.1,
	                    backgroundColor:barColors,
	                    borderColor: "rgba(75,192,192,1)",
	                    borderCapStyle: 'butt',
	                    borderDash: [],
	                    borderDashOffset: 0.0,
	                    borderJoinStyle: 'miter',
	                    pointBorderColor: "rgba(75,192,192,1)",
	                    pointBackgroundColor: "#fff",
	                    pointBorderWidth: 1,
	                    pointHoverRadius: 5,
	                    pointHoverBackgroundColor: "rgba(52, 152, 219,1)",
	                    pointHoverBorderColor: "rgba(220,220,220,1)",
	                    pointHoverBorderWidth: 2,
	                    pointRadius: 1,
	                    pointHitRadius: 10,
						fontSize: '20',
	                    data: [],
	                    spanGaps: false,
	                }
	            ]
	        },
	        options: {
	            tooltips: {
	                mode: 'index',
	                intersect: false
	            },
				
				 /*legend: {
				            labels: {
				                // This more specific font property overrides the global property
				                fontColor: 'red'
				            }
				        }*/
	            scales: {
	                 y: {
					      ticks: {
					        // make the original labels white for later painting over with custom sub-labels
					        color: "blacl",
					        // we still want this here to be able to take up the same space as the eventual label we will stick here
					        font: {
					          size: 22,
					          weight: "bold"
					        }
					      }
					    },
					 x: {
					      ticks: {
					        // make the original labels white for later painting over with custom sub-labels
					        color: "blacl",
					        // we still want this here to be able to take up the same space as the eventual label we will stick here
					        font: {
					          size: 18,
					          weight: "bold"
					        }
					      }
					    },
	            }
	        }
    });
	
	
	ajax_chart(myChart);

	
	 function ajax_chart(chart) {
	        
		       $.ajax({
				    url: "/vendor/portal/get_rating",
					type: 'GET',
					async:false, 
					  }).done(function(data) {
							data = JSON.parse(data)
							chart.data.labels = data.labels;
				            chart.data.datasets[0].data = data.data.rates; // or you can iterate for multiple datasets
							chart.update(); // finally update our chart

							
					  }).fail(function() {

						bootbox.alert("unable to load chat data");

				  });
			
	    }
	});
	
	
	
})

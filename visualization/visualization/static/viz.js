'use strict';

var xmlhttp = new XMLHttpRequest();
xmlhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        var dat = JSON.parse(this.responseText);
		techViews_SVG(dat.tech_views)
		// userKeywords_SVG(dat.user_keywords)
		// techKeywords_SVG(dat.tech_keywords)

    }
};

var universityId = window.location.pathname.substring(window.location.pathname.lastIndexOf("/") + 1);
xmlhttp.open("GET", window.location.origin + "/university/data/" + universityId, true);
xmlhttp.setRequestHeader("Access-Control-Allow-Origin","*");
xmlhttp.send();


function techViews_SVG(techViews) { // generate bar chart based on the count of views on each technology


	console.log(techViews)

	var margin = {top: 20, right: 20, bottom: 70, left: 40},
    	width = 600 - margin.left - margin.right,
    	height = 300 - margin.top - margin.bottom;
	
	// ordinal scale function 
    var xScale = d3.scaleBand()
    				.rangeRound([0, width])
    				.padding(.2)
    				.domain(techViews.map(function(d) { return d.TechID; }));


    // linear scale function
    var yScale = d3.scaleLinear()
    				.range([height, 0])
    				.domain([0, d3.max(techViews, function(d) { return d.Views; })]);


	var svgContainer = d3.select("body")
						.append("svg")
						.attr("height", "100%")
						.attr("width", "100%")
						.attr("class", "svgContainer")
						.append("g")
						.attr("transform", "translate(" + margin.left + "," + margin.top + ")"); //add a g element that provides a reference point for adding axes
	

	//append x axis
	svgContainer.append("g")
      			.attr("class", ".axis")
      			.attr("transform", "translate(0," + height + ")")
      			.call(d3.axisBottom(xScale))
    			.selectAll("text")
      			.style("text-anchor", "end")
      			.attr("dx", "1em")


	
    //append y axis
    svgContainer.append("g")
      			.attr("class", ".axis")
      			.call(d3.axisLeft(yScale).ticks(10))
    			.append("text")
      			.attr("transform", "rotate(-90)")
      			.attr("dy", ".71em")
      			.style("text-anchor", "end")


    var bars = svgContainer.selectAll("bar")
      						.data(techViews)
    						.enter()
    						.append("rect")
    
    var barAttr = bars.attr("class", "bar")
    					.attr("x", function(d) {return xScale(d.TechID); })
    					.attr("width", xScale.bandwidth())
    					.attr("y", function(d) {return yScale(d.Views); })
    					.attr("height", function(d){return height - yScale(d.Views); });

 //      .style("fill", "steelblue")
 //      .attr("x", function(d) { return x(d.date); })
 //      .attr("width", x.rangeBand())
 //      .attr("y", function(d) { return y(d.value); })
 //      .attr("height", function(d) { return height - y(d.value); });
	// var bars = svgContainer.selectAll("rect")
	// 					.data(techViews)
	// 					.enter()
	// 					.append("rect");

 //    var barAttr = bars.attr("class", "bar")
 //    					.attr("x", function(d,i){return i*60;})
 //    					.attr("y", function(d, i){return 500 - d.Views * 10})
 //    					.attr("width", 20)
 //    					.attr("height", function(d, i){return d.Views *10})

    // var labels = svgContainer.selectAll("text")
    // 						.data(techViews)
    // 						.enter()
    // 						.append("text")
    // 						.text(function(d){return d.id})

    // var labelAttr = labels.attr("class", "text")
    //        					.attr("x", function(d, i) {return i * 60 })
    //       					.attr("y", function(d, i) {return 500 - (d.Views * 10)});

}


function userKeywords_SVG(userKeywords) { // generate circle packing based on the keywords of users viewing the technologies published by the university
	console.log(userKeywords)
}


function techKeywords_SVG(techKeywords){ // generate bubble chart based on the keywords crossing all technologies published by the university
	console.log(techKeywords)
}

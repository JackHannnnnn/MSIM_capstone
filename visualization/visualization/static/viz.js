'use strict';

var xmlhttp = new XMLHttpRequest();
xmlhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        var dat = JSON.parse(this.responseText);
		techViews_SVG(dat.tech_views)
		userKeywords_SVG(dat.user_keywords)
		// techKeywords_SVG(dat.tech_keywords)

    }
};

var universityId = window.location.pathname.substring(window.location.pathname.lastIndexOf("/") + 1);
xmlhttp.open("GET", window.location.origin + "/university/data/" + universityId, true);
xmlhttp.setRequestHeader("Access-Control-Allow-Origin","*");
xmlhttp.send();


function techViews_SVG(techViews) { // generate bar chart based on the count of views on each technology


	console.log(techViews)

  var svgContainer = d3.select("body")
            .append("svg")
            .attr("height", "500")
            .attr("width", "960")
            .attr("class", "svgContainer")


  var margin = {top: 20, right: 20, bottom: 30, left: 40},
      width = svgContainer.attr("width") - margin.left - margin.right,
      height = svgContainer.attr("height") - margin.top - margin.bottom;

  

  var g = svgContainer.append("g")
                      .attr("transform", "translate(" + margin.left + "," + margin.top + ")"); //add a g element that provides a reference point for adding axes
  
	
	// ordinal scale function 
  var xScale = d3.scaleBand()
  				.rangeRound([0, width])
  				.padding(.5)
  				.domain(techViews.map(function(d) { return d.TechID; }));


  // linear scale function
  var yScale = d3.scaleLinear()
  				.rangeRound([height, 0])
  				.domain([0, d3.max(techViews, function(d) { return d.Views; })]);


		

	//append x axis
	g.append("g").attr("class", ".axis")
		            .attr("transform", "translate(0," + height + ")")
		            .call(d3.axisBottom(xScale))
              	// .selectAll("text")
              	// 	.style("text-anchor", "end")
              	// 	.attr("dx", "1em")


	
    //append y axis
    g.append("g").attr("class", ".axis")
      			     .call(d3.axisLeft(yScale).ticks(10))
    			       // .append("text")
            		//  .attr("transform", "rotate(-90)")
              //   .attr("y", 6)
              //   .attr("dy", "0.71em")
              //   .attr("text-anchor", "end")
              //   .text("Views");

    var bars = g.selectAll("bar")
      						.data(techViews)
    						.enter()
    						.append("rect")
    
    var barAttr = bars.attr("class", "bar")
    					.attr("x", function(d) {return xScale(d.TechID); })
    					.attr("width", xScale.bandwidth())
    					.attr("y", function(d) {return yScale(d.Views); })
    					.attr("height", function(d){return height - yScale(d.Views); });

}


function userKeywords_SVG(userKeywords) { // generate circle packing based on the keywords of users viewing the technologies published by the university
	console.log(userKeywords)

  var svgContainer = d3.select("body")
                        .append("svg")
                        .attr("height", "800")
                        .attr("width", "800")
                        .attr("class", "svgContainer")


  var diameter = svgContainer.attr("height");

  var g = svgContainer.append("g")
                    .attr("transform", "translate(2,2)")

  
  var format = d3.format(",d")

  var pack = d3.pack()
        .size([diameter -4, diameter-4])
        .padding(10)


  var root = d3.hierarchy(userKeywords).sum(function(d) { return d.size; })
  var node = g.selectAll(".node")
                .data(pack(root).descendants())
                .enter()
                .append("g")
                .attr("class", "node")
                .attr("class", function(d) { return d.children ? "node" : "leaf node"; })
                .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

  node.append("title")
      .text(function(d) { return d.data.name + "\n" + format(d.value); });

  node.append("circle")
      .attr("r", function(d) { return d.r; });

  node.filter(function(d) { return !d.children; }).append("text")
      .attr("dy", "0.3em")
      .attr("dx", "-0.7em")
      .text(function(d) {return d.data.name})

}


function techKeywords_SVG(techKeywords){ // generate bubble chart based on the keywords crossing all technologies published by the university
	console.log(techKeywords)
}

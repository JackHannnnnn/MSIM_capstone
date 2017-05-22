'use strict';
console.log("viz_all_university running")
var xmlhttp = new XMLHttpRequest();
xmlhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        var dat = JSON.parse(this.responseText);
        techViews_SVG(dat.tech_views_all) // bar chart
        emailsSentAll_SVG(dat.emails_sent_all) //bar chart
    }
};

//var universityId = window.location.pathname.substring(window.location.pathname.lastIndexOf("/") + 1);
console.log("before")
xmlhttp.open("GET", window.location.origin + "/all/data", true);
console.log("after")
xmlhttp.setRequestHeader("Access-Control-Allow-Origin","*");
xmlhttp.send();

function techViews_SVG(techViews) { // generate bar chart based on the count
// of views on each technology
    console.log(techViews.slice(0,10))
    techViews = techViews.slice(0, 10)
    var svgContainer = d3.select("body")
            .append("svg")
            .attr("height", "400")
            .attr("width", "600")
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

  //append y axis
    g.append("g").attr("class", ".axis")
    			     .call(d3.axisLeft(yScale).ticks(10))
               .append("text")
               .attr("transform", "rotate(-90)")
               .attr("y", 6)
               .attr("dy", ".71em")
               .attr("text-anchor", "end")
               .attr("fill", "#000")
               .text("Counts")

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

function emailsSentAll_SVG(emails_sent_all){
     console.log(emails_sent_all.slice(0,10))
     emails_sent_all = emails_sent_all.slice(0, 10)
     var svgContainer = d3.select("body")
            .append("svg")
            .attr("height", "400")
            .attr("width", "600")
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
  				.domain(emails_sent_all.map(function(d) { return d.Technology;
  				}));


  // linear scale function
    var yScale = d3.scaleLinear()
  				.rangeRound([height, 0])
  				.domain([0, d3.max(emails_sent_all, function(d) { return d
  				.Sent; })]);


	//append x axis
    g.append("g").attr("class", ".axis")
		            .attr("transform", "translate(0," + height + ")")
		            .call(d3.axisBottom(xScale))

  //append y axis
    g.append("g").attr("class", ".axis")
    			     .call(d3.axisLeft(yScale).ticks(10))
               .append("text")
               .attr("transform", "rotate(-90)")
               .attr("y", 6)
               .attr("dy", ".71em")
               .attr("text-anchor", "end")
               .attr("fill", "#000")
               .text("Email Sent")

    var bars = g.selectAll("bar")
      					.data(emails_sent_all)
    					.enter()
    					.append("rect")

    var barAttr = bars.attr("class", "bar")
    					.attr("x", function(d) {return xScale(d.Technology); })
    					.attr("width", xScale.bandwidth())
    					.attr("y", function(d) {return yScale(d.Sent); })
    					.attr("height", function(d){return height - yScale(d
    					.Sent); });

}

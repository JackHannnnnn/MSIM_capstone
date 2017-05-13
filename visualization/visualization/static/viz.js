'use strict';

var xmlhttp = new XMLHttpRequest();
xmlhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        var dat = JSON.parse(this.responseText);
		techViews_SVG(dat.tech_views) // bar chart
    emailSentVsClick(dat.emails) // group bar chart
		userKeywords_SVG(dat.user_keywords)
		techKeywords_SVG(dat.tech_keywords)
    matchUsers(dat.matches)
    viewedusers(dat.viewed_users)
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


function userKeywords_SVG(userKeywords) { // generate circle packing based on the keywords of users viewing the technologies published by the university
	console.log(userKeywords)

  var svgContainer = d3.select("body")
                        .append("svg")
                        .attr("height", "600")
                        .attr("width", "600")
                        .attr("class", "svgContainer")


  var diameter = +svgContainer.attr("height");

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
	console.log(techKeywords.slice(0,10))
     var svgContainer = d3.select("body")
                        .append("svg")
                        .attr("height", "600")
                        .attr("width", "600")
                        .attr("class", "svgContainer");

    var diameter = 600;
    var max_count = d3.max(techKeywords, function(d){
        return d.Count;
    });
    var color = d3.scaleLinear()
                    .domain([1, max_count])
                    .range(["beige","red"]);

    var bubble = d3.pack(techKeywords)
            .size([diameter, diameter])
            .padding(1.5);
    var nodes = d3.hierarchy({children:techKeywords.slice(0,10)})
            .sum(function(d) { return d.Count; });
            
    var node = svgContainer.selectAll(".node")
            .data(bubble(nodes).descendants())
            .enter()
            .filter(function(d){
                return  !d.children
            })
            .append("g")
            .attr("class", "node")
            .attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            });

    node.append("title")
            .text(function(d) {
                return d.keyword + ": " + d.Count;
            });
    node.append("circle")
            .attr("r", function(d) {
                return d.r;
            })
            .style("fill", function(d) {
                return color(d.value);
            });

    node.append("text")
            .attr("dy", ".3em")
            .style("text-anchor", "middle")
            .text(function(d) {
                return d.data.keyword + ": " + d.data.Count;
            });

    d3.select(self.frameElement)
            .style("height", diameter + "px");



}

function viewedusers(viewedUsers){ // generate an html table showing the users that viewed each technology
    console.log(viewedUsers)
    var columns = ["Technology", "Company"]


    var table = d3.select("body")
                  .append("table")

    var thead = table.append("thead")
    var tbody = table.append("tbody") 

    // // append the header row
    thead.append("tr")
          .selectAll("th")
          .data(columns)
          .enter()
          .append("th")
          .text(function(column){ return column;})
                  

    var nested = d3.nest()
                  .key(function(d){ return d.Technology;})
                  .entries(viewedUsers)
    console.log(nested)

    nested.forEach(function (d) {
    var rowspan = d.values.length;
    d.values.forEach(function (val, index) {
        var tr = thead.append("tr");
        if (index == 0) { //rowspan only for first element
            tr.append("td")
                .attr("rowspan", rowspan)
                .text(val.Technology);
        }
        tr.append("td")
            .text(val.Company);


    });
});
          

}

function emailSentVsClick(emailData){ // generate a group bar chart showing counts of email sent vs email clicks on each technology
 
  console.log(emailData)


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


  var x0 = d3.scaleBand()
    .rangeRound([0, width])
    .paddingInner(0.3)
    .domain(emailData.map(function(d) {return d.Technology}));

  var keys = d3.keys(emailData[0]).filter(function(key) { return key !== "Technology"; });

 emailData.forEach(function(d) {
    d.values = keys.map(function(name) { return {label: name, value: +d[name]}; });
    console.log(d.values)
});
  
  var x1 = d3.scaleBand()
    .padding(0.15)
    .rangeRound([0, x0.bandwidth()])
    .domain(keys);  
  
  
  var y = d3.scaleLinear().rangeRound([height, 0])
            .domain([0, d3.max(emailData, function(d) { return d3.max(d.values, function(d) { return d.value; }); })])

  var z = d3.scaleOrdinal().range(["#a05d56" , "#8a89a6"])


g.append("g")
      .attr("class", ".axis")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x0));


g.append("g").attr("class", ".axis")
             .call(d3.axisLeft(y).ticks(10))
             .append("text")
             .attr("transform", "rotate(-90)")
             .attr("y", 6)
             .attr("dy", ".71em")
             .attr("text-anchor", "end")
             .attr("fill", "#000")
             .text("Counts")

var bar = g.append("g")
    .selectAll(".bar")
    .data(emailData)
    .enter().append("g")
    .attr("class", ".bar")
    .attr("transform", function(d) { return "translate(" + x0(d.Technology) + ",0)"; });

bar.selectAll("rect")
  .data(function(d){return d.values;})
  .enter()
  .append("rect")
  .attr("class", "gbar")
  .attr("width", x1.bandwidth())
  .attr("x", function(d){return x1(d.label);})
  .attr("y", function(d){return y(d.value);})
  .attr("fill", function(d){return z(d.label);})
  .attr("height", function(d){return height-y(d.value);})

var legend = g.append("g")
      .attr("font-family", "sans-serif")
      .attr("font-size", 10)
      .attr("text-anchor", "end")
    .selectAll("g")
    .data(keys)
    .enter().append("g")
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

  legend.append("rect")
      .attr("x", width - 19)
      .attr("width", 19)
      .attr("height", 19)
      .attr("fill", z);

  legend.append("text")
      .attr("x", width - 24)
      .attr("y", 9.5)
      .attr("dy", "0.32em")
      .text(function(d) { return d; });
}

function matchUsers(matchUsers){ // add an html table showing the top 5 most relevant users to each technology
  console.log(matchUsers)
  var table =  d3.select("body").append("table"),
      thead = table.append("thead"),
      tbody = table.append("tbody")

 thead.selectAll("th")
      .data(matchUsers.map(function(d){return d.Technology})) // technology list
      .enter()
      .append("th")
      .text(function(d){return d})

  var td = tbody.selectAll("td")
              .data(matchUsers)
              .enter()
              .append("td")

  td.selectAll("tr")
      .data(function(d){return d.Matches})
      .enter()
      .append("tr")
      .style("line-height", "30px")
      .text(function(d){return d})
}
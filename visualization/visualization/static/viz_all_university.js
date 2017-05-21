'use strict';
console.log(111)
var xmlhttp = new XMLHttpRequest();
xmlhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        var dat = JSON.parse(this.responseText);
        console.log(dat.tech_views)
//		techViews_SVG(dat.tech_views) // bar chart
    }
};

//var universityId = window.location.pathname.substring(window.location.pathname.lastIndexOf("/") + 1);
xmlhttp.open("GET", window.location.origin + "/all/university/data/", true);
xmlhttp.setRequestHeader("Access-Control-Allow-Origin","*");
xmlhttp.send();
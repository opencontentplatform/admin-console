(function (global, factory) {
	typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
	typeof define === 'function' && define.amd ? define(['exports'], factory) :
	(factory((global.ocp_many = global.ocp_many || {})));
}(this, (function (exports) { 'use strict';


function exec(jsonData) {
	// Set the dimensions and margins of the diagram
	var margin = {top: 35, right: 90, bottom: 30, left: 90},
		width = 1024 - margin.left - margin.right,
		height = 900 - margin.top - margin.bottom;

	var svg = d3.select("body")
		.append("svg")
		.attr("preserveAspectRatio", "xMinYMin meet")
		.attr("viewBox", "0 0 " + width + " " + height)
		.classed("svg-content-responsive", true);

	// Add tooltip div
	var toolTip = d3.select("body").append("div")
		.attr("class", "tooltip")
		.attr("data-html", "true")
		.style("opacity", 1e-6);

	// Need to use "first_id" and "second_id" for links instead of D3's default
	// attributes "source" and "target"
	jsonData.links.forEach(function(d){
		d.source = d.first_id;
		d.target = d.second_id;
		console.log('setting source and target: ', d);
		}
	);

	// Add zoom capabilities
	var zoom_handler = d3.zoom()
		.on("zoom", zoom_actions);
	zoom_handler(svg);
	function zoom_actions(){
		g.attr("transform", d3.event.transform);
	}

	// Pattern section for icon display
	// ---------------------------------------------------------------------- //
	var defs = svg.append("defs");

	defs.append('pattern')
		.attr("id", "linux")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/linux-100.png")
		.attr("width", 50)
		.attr("height", 50)
		.attr("y", 4)
		.attr("x", 6);

	defs.append('pattern')
		.attr("id", "windows")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-windows8-26.svg")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 7)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "softwaredots")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/software-dots-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 8);

	defs.append('pattern')
		.attr("id", "software")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/software-50.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 8);

	defs.append('pattern')
		.attr("id", "file")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/file-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 8);

	defs.append('pattern')
		.attr("id", "simple")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/simple-square-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "ip")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-web-address-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "dns_record")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-contact-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "dns_domain")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-hierarchy-100.png")
		.attr("width", 45)
		.attr("height", 45)
		.attr("x", 8)
		.attr("y", 3);

	defs.append('pattern')
		.attr("id", "process")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/gears-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "process_group")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-automatic-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "model_object")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-camera-addon-identification-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

		defs.append('pattern')
		.attr("id", "port")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/port-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "application")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-apple-app-store-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "environment")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-escape-mask-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "location")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-treasure-map-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);

	defs.append('pattern')
		.attr("id", "collection")
		.attr("width", 1)
		.attr("height", 1)
		.append("svg:image")
		.attr("xlink:href", "./static/icons/icons8-module-100.png")
		.attr("width", 40)
		.attr("height", 40)
		.attr("x", 10)
		.attr("y", 10);
	// ---------------------------------------------------------------------- //


	// Setup the simulation and add forces
	var simulation = d3.forceSimulation(jsonData.objects)
		.force("charge_force", d3.forceManyBody().strength(-100))
		.force("colide_force", d3.forceCollide().radius(50))
		// Need to use "identifier" on objects instead of D3's default of "id"
		//.force("link_force", d3.forceLink(jsonData.links).distance(100).strength(1))
		.force("link_force", d3.forceLink(jsonData.links).id(function(d) { return d.identifier; }).distance(100).strength(1))
		.force("center_force", d3.forceCenter(width / 2, height / 2))
		.on("tick", ticked);

	//var CSS_COLOR_NAMES = ["AliceBlue","AntiqueWhite","Aqua","Aquamarine","Azure","Beige","Bisque","Black","BlanchedAlmond","Blue","BlueViolet",
	//     "Brown","BurlyWood","CadetBlue","Chartreuse","Chocolate","Coral","CornflowerBlue","Cornsilk","Crimson","Cyan","DarkBlue","DarkCyan",
	//     "DarkGoldenRod","DarkGray","DarkGrey","DarkGreen","DarkKhaki","DarkMagenta","DarkOliveGreen","Darkorange","DarkOrchid","DarkRed",
	//     "DarkSalmon","DarkSeaGreen","DarkSlateBlue","DarkSlateGray","DarkSlateGrey","DarkTurquoise","DarkViolet","DeepPink","DeepSkyBlue",
	//     "DimGray","DimGrey","DodgerBlue","FireBrick","FloralWhite","ForestGreen","Fuchsia","Gainsboro","GhostWhite","Gold","GoldenRod","Gray","Grey",
	//     "Green","GreenYellow","HoneyDew","HotPink","IndianRed","Indigo","Ivory","Khaki","Lavender","LavenderBlush","LawnGreen","LemonChiffon",
	//     "LightBlue","LightCoral","LightCyan","LightGoldenRodYellow","LightGray","LightGrey","LightGreen","LightPink","LightSalmon","LightSeaGreen",
	//     "LightSkyBlue","LightSlateGray","LightSlateGrey","LightSteelBlue","LightYellow","Lime","LimeGreen","Linen","Magenta","Maroon","MediumAquaMarine",
	//     "MediumBlue","MediumOrchid","MediumPurple","MediumSeaGreen","MediumSlateBlue","MediumSpringGreen","MediumTurquoise","MediumVioletRed",
	//     "MidnightBlue","MintCream","MistyRose","Moccasin","NavajoWhite","Navy","OldLace","Olive","OliveDrab","Orange","OrangeRed","Orchid",
	//     "PaleGoldenRod","PaleGreen","PaleTurquoise","PaleVioletRed","PapayaWhip","PeachPuff","Peru","Pink","Plum","PowderBlue","Purple","Red",
	//     "RosyBrown","RoyalBlue","SaddleBrown","Salmon","SandyBrown","SeaGreen","SeaShell","Sienna","Silver","SkyBlue","SlateBlue","SlateGray","SlateGrey",
	//     "Snow","SpringGreen","SteelBlue","Tan","Teal","Thistle","Tomato","Turquoise","Violet","Wheat","White","WhiteSmoke","Yellow","YellowGreen"];

	// Colors subset that works nice for status fills on white icons:
	//     BurlyWood, CadetBlue, Coral, CornflowerBlue, DarkKhaki,
	//     DarkSeaGreen, Gainsboro, IndianRed, LightSeaGreen, LightSalmon
	//     LightGray, LightBlue, LightCoral, MediumAquaMarine, LightSkyBlue
	//     Moccasin, PaleVioletRed, Peru, Plum, PowderBlue, Sienna, Silver,
	//     SkyBlue, SlateGray, SteelBlue, Tan, Thistle
	function colorStatus(d){
		if (d.status == "3"){
			return "Coral";
		} else if (d.status == "2") {
			return "CornflowerBlue";
		} else if (d.status == "1") {
			return "MediumAquaMarine";
		} else {
			return "SlateGray";
		}
	}
	function fillImage(d){
		if (d.class_name == "Linux"){
			return "url(#linux)";
		} else if (d.class_name == "Windows") {
			return "url(#windows)";
		} else if (d.class_name == "FileCustom") {
			return "url(#file)";
		} else if (d.class_name == "SoftwarePackage") {
			return "url(#softwaredots)";
		} else if (d.class_name == "SoftwareFingerprint") {
			return "url(#software)";
		} else if (d.class_name == "ProcessFingerprint") {
			return "url(#process)";
		} else if (d.class_name == "ModelObject") {
			return "url(#model_object)";
		} else if (d.class_name == "ProcessSignature") {
			return "url(#process_group)";
		} else if (d.class_name == "TcpIpPort") {
			return "url(#port)";
		} else if (d.class_name == "IpAddress") {
			return "url(#ip)";
		} else if (d.class_name == "NameRecord") {
			return "url(#dns_record)";
		} else if (d.class_name == "Domain") {
			return "url(#dns_domain)";
		} else if (d.class_name == "BusinessApplication") {
			return "url(#application)";
		} else if (d.class_name == "LocationGroup") {
			return "url(#location)";
		} else if (d.class_name == "SoftwareGroup") {
			return "url(#collection)";
		} else if (d.class_name == "EnvironmentGroup") {
			return "url(#environment)";
		} else {
			return "url(#simple)";
		}
	}

	// Add group for the zoom
	var g = svg.append("g")
		.attr("class", "everything");

	var link = g.selectAll()
		.data(jsonData.links)
		.enter()
		.append("line")
		.style("stroke", "#ccc")
		.style("stroke-width", 1);


	var node = g.selectAll()
		.data(jsonData.objects, function(d) {return d.identifier;})
		.enter()
		.append("g")
		.call(d3.drag()
			.on("start", dragstarted)
			.on("drag", dragged)
			.on("end", dragended));

	node.append("circle")
		.attr("r", 30)
		.style("fill", colorStatus);

	node.append("circle")
		.attr("r", 30)
		.attr("stroke", "#ccc")
		.attr("stroke-width", "2px")
		.attr("fill", fillImage)
		.on("mouseover", mouseover)
		.on("mousemove", function(d) {mousemove(d);})
		.on("mouseout", mouseout);

	// Float labels
	node.append("text")
		.style("fill", "black")
		.style("font", "14px sans-serif")
		.attr("dx", -30)
		.attr("dy", 45)
		.text(function(d) { return d.data.caption; });


	function ticked() {
		link.attr("x1", function(d) { return d.source.x; })
			.attr("y1", function(d) { return d.source.y; })
			.attr("x2", function(d) { return d.target.x; })
			.attr("y2", function(d) { return d.target.y; });
		node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")";});
	}

	function mouseover() {
		console.log('mouseover');
		toolTip.transition()
			.duration(300)
			.style("opacity", 0.8);
	}
	function mousemove(d) {
		console.log('mousemove: ', d);
		toolTip
		.text(function() {
			var dictionary = d.data;
			var tmp = "";
			for (var key in dictionary) {
				if (dictionary.hasOwnProperty(key)) {
					tmp += key + ": " + dictionary[key] + '\n';
				}
			}
			tmp += "id: " + d.identifier + '\n';
			return tmp;
		})
		.style("left", (d3.event.pageX ) + "px")
		.style("top", (d3.event.pageY) + "px");
	}
	function mouseout() {
		console.log('mouseout');
		toolTip.transition()
			.duration(300)
			.style("opacity", 1e-6);
	}

	function dragstarted(d) {
		if (!d3.event.active) simulation.alphaTarget(0.3).restart();
		d.fx = d.x;
		d.fy = d.y;
	}

	function dragged(d) {
		d.fx = d3.event.x;
		d.fy = d3.event.y;
	}

	function dragended(d) {
		if (!d3.event.active) simulation.alphaTarget(0);
		d.fx = null;
		d.fy = null;
	}

}
	// Expose the function for external calls
	exports.exec = exec;
})));

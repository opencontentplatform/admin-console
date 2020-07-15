(function (global, factory) {
	typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
	typeof define === 'function' && define.amd ? define(['exports'], factory) :
	(factory((global.ocp_tree = global.ocp_tree || {})));
}(this, (function (exports) { 'use strict';


function exec(jsonData) {
	console.log('OCP TREE: ', jsonData)
	// Set the dimensions and margins of the diagram
	var margin = {top: 35, right: 90, bottom: 30, left: 90},
		width = 1024 - margin.left - margin.right,
		height = 900 - margin.top - margin.bottom;

	var svg = d3.select("body")
		.append("svg")
		.attr("preserveAspectRatio", "xMinYMin meet")
		.attr("viewBox", "0 0 " + width + " " + height)
		.classed("svg-content-responsive", true)
		.append("g")
		.attr("transform", "translate(0," + margin.top + ")");

	// Add tooltip div
	var toolTip = d3.select("body").append("div")
		.attr("class", "tooltip")
		.attr("data-html", "true")
		.style("opacity", 1e-6);

	// Added rectangle so zoom & pan work on white space too
	svg.append("rect")
		.attr("class", "overlay")
		.attr("width", width)
		.attr("height", height);

	// Add encompassing group for the viewpane
	var viewpane = svg.append("g");

	// Zoom capabilities
	svg.call(d3.zoom()
			.scaleExtent([0.25, 2.0])
			.on("zoom", zoomed));
	function zoomed() {
		viewpane.attr("transform", d3.event.transform);
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
		//icons8-hierarchy-100
		//icons8-camera-addon-identification-100

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
		if (d.data.status == "3"){
			return "Black";
		} else if (d.data.status == "2") {
			return "Gray";
		} else if (d.data.status == "1") {
			return "DarkGray";
		} else {
			return "CornflowerBlue";
		}
	}
	function fillImage(d){
		if (d.data.class_name == "Linux"){
			return "url(#linux)";
		} else if (d.data.class_name == "Windows") {
			return "url(#windows)";
		} else if (d.data.class_name == "SoftwareFingerprint") {
			return "url(#software)";
		} else if (d.data.class_name == "ProcessFingerprint") {
			return "url(#process)";
		} else if (d.data.class_name == "ModelObject") {
			return "url(#model_object)";
		} else if (d.data.class_name == "ProcessSignature") {
			return "url(#process_group)";
		} else if (d.data.class_name == "TcpIpPort") {
			return "url(#port)";
		} else if (d.data.class_name == "IpAddress") {
			return "url(#ip)";
		} else if (d.data.class_name == "BusinessApplication") {
			return "url(#application)";
		} else if (d.data.class_name == "LocationGroup") {
			return "url(#location)";
		} else if (d.data.class_name == "SoftwareGroup") {
			return "url(#collection)";
		} else if (d.data.class_name == "EnvironmentGroup") {
			return "url(#environment)";
		} else {
			return "url(#simple)";
		}
	}

	// Extraneous variables
	var i = 0;
	var	duration = 750;

	// Declare a tree layout and assign the size
	var treemap = d3.tree().size([height, width]);

	// Assign parent, children, height, depth
	var root = d3.hierarchy(jsonData, function(d) { return d.children; });
	root.x0 = height / 2;
	root.y0 = 0;

	update(root);


	function update(source) {
		// Assigns the x and y position for the nodes
		var treeData = treemap(root);
		var nodes = treeData.descendants();
		var links = nodes.slice(1);

		// Normalize for fixed-depth on screen; the 30 is for the bottom icon height
		var normalizedDepth = (height / root.height) - 30;
		// Transform OCP content into the D3 nodes
		nodes.forEach(function(d){
			d.y = d.depth * normalizedDepth;
			d.id = d.identifier;
			d.status = d.status || (d.status = 0);
			}
		);

		// Node section
		// ---------------------------------------------------------------------- //
		var node = viewpane.selectAll('g.node')
			.data(nodes, function(d) {return d.id || (d.id = ++i); });
		// Enter new nodes at the parent's previous position
		var nodeEnter = node.enter()
			.append('g')
			.attr("class", function(d) { return "node" + (d.children ? " node--internal" : " node--leaf"); })
			.attr("transform", function() { return "translate(" + source.x0 + "," + source.y0 + ")";})
			.on('click', click);
		nodeEnter.append("circle")
			.attr("r", 30)
			.attr("stroke", "#ccc")
			.attr("stroke-width", function(d) { return d._children ? "5px" : "2px"; })
			.style("fill", colorStatus);
		nodeEnter.append("circle")
			.attr("r", 30)
			.attr("fill", fillImage)
			.on("mouseover", mouseover)
			.on("mousemove", function(d){mousemove(d);})
			.on("mouseout", mouseout);
		nodeEnter.append("text")
			.style("fill", "#333")
			.style("font", "14px sans-serif")
			.attr("dx", -30)
			.attr("dy", 45)
			.text(function(d) { console.log('===>', d.data.data); return d.data.data.caption;});

		// Update nodes
		var nodeUpdate = nodeEnter.merge(node);
		nodeUpdate.transition()
			.duration(duration)
			.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
		nodeUpdate.select("circle")
			.attr("r", 30)
			.attr("stroke", "#ccc")
			.attr("stroke-width", function(d) { return d._children ? "5px" : "2px"; })
			.style("fill", colorStatus);
		nodeUpdate.select("circle")
			.attr("r", 30)
			.attr("fill", fillImage);

		// Remove nodes
		var nodeExit = node.exit().transition()
			.duration(duration)
			.attr("transform", function() { return "translate(" + source.x + "," + source.y + ")"; })
			.remove();
		nodeExit.select('circle')
			.attr('r', 1e-6);
		nodeExit.select('text')
			.style('fill-opacity', 1e-6);
		// ---------------------------------------------------------------------- //


		// Link section
		// ---------------------------------------------------------------------- //
		var link = viewpane.selectAll('path.link')
			.data(links, function(d) { return d.id; });
		// Enter new links at the parent's previous position
		var linkEnter = link.enter().insert('path', 'g')
			.style("stroke", "#ccc")
			.style("stroke-width", 1)
			.attr("class", "link")
			.attr('d', function(){
				var o = {x: source.x0, y: source.y0};
				return diagonal(o, o);
			});

		// Update links
		var linkUpdate = linkEnter.merge(link);
		// Transition back to the parent element position
		linkUpdate.transition()
			.duration(duration)
			.attr('d', function(d){ return diagonal(d, d.parent);});

		// Remove links
		var linkExit = link.exit().transition()
			.duration(duration)
			.attr('d', function() {
				var o = {x: source.x, y: source.y};
				return diagonal(o, o);
			})
			.remove();
		// ---------------------------------------------------------------------- //


		// Store old positions for transition
		nodes.forEach(function(d){
			d.x0 = d.x;
			d.y0 = d.y;
		});

		// Create diagonal path from parent to child nodes
		function diagonal(s, d) {
			var path = "M" + s.x + "," + s.y + "," + "C" + s.x + "," + (s.y + d.y) / 2 + " " + d.x + "," + (s.y + d.y) / 2 + " " + d.x + "," + d.y;
			return path;
		}

		// Toggle children on click
		function click(d) {
			if (d.children) {
				d._children = d.children;
				d.children = null;
			} else {
				d.children = d._children;
				d._children = null;
			}
			update(d);
		}

		// Toggle tooltip with mouse events
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
				var dictionary = d.data.data;
				var tmp = "";
				for (var key in dictionary) {
					if (dictionary.hasOwnProperty(key)) {
						tmp += key + ": " + dictionary[key] + '\n';
					}
				}
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
	}
}

    // Expose the function for external calls
	exports.exec = exec;
})));

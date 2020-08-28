(function (global, factory) {
	typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
	typeof define === 'function' && define.amd ? define(['exports'], factory) :
	(factory((global.ocp_calendar = global.ocp_calendar || {})));
}(this, (function (exports) { 'use strict';


	function exec(jsonData) {
		// Initialize ranges
		var dateRangeMin = d3.min(jsonData, function(d){
			var start = parseISO8601(d.time_started);
			return d3.timeDay.floor(start[0]);
			}
		);
		var dateRangeMax = d3.max(jsonData, function(d){
			var stop = parseISO8601(d.time_finished);
			return d3.timeDay.ceil(stop[0]);
			}
		);
		var dateRange = [dateRangeMin, dateRangeMax];
		var hourRange = [0, 24];
		// Initialize layout
		var margin = {top: 35, right: 90, bottom: 30, left: 90};
		var width = window.innerWidth * 0.8;
		var barHeight = 30;
		var height = ((dateRangeMax - dateRangeMin) / (24*60*60*1000)) * barHeight;
		// Initialize chart section
		var svg = d3.select("body").append("div")
			.selectAll("svg").data(d3.range(1))
				.enter()
				.append("svg")
				.attr("width", width + margin.right + margin.left)
				.attr("height", height + margin.top + margin.bottom)
				.append("g")
				.attr('transform', 'translate(' + margin.left + ', ' + margin.top + ')');

		// Define the div for the tooltip
		var toolTip = d3.select("body").append("div")
			.attr("class", "tooltip")
			.style("opacity", 0);

		// Scale grid by 24 hours (timeHour)
		var gridScale = d3.scaleTime()
			.range([0, width]);
		// Scale X by 24 hours (int)
		var xScale = d3.scaleTime()
			.domain(hourRange)
			.range([0, width]);
		// Scale Y by jsonData (dates)
		var yScale = d3.scaleTime()
			.domain(dateRange)
			.range([0, height]);

		// Add the X and Y axis lines
		svg.append("g")
			.call(d3.axisTop(gridScale)
				  .tickArguments([d3.timeHour.every(3)])
				  .tickFormat(d3.timeFormat("%I %p"))
				  );
		svg.append("g")
			.call(d3.axisLeft(yScale)
				  .ticks(height / barHeight)
			);

		// Add the gridlines
		function make_x_gridlines() {
			return d3.axisBottom(gridScale);
		}
		function make_y_gridlines() {
			return d3.axisLeft(yScale)
					.ticks(height / barHeight);
		}
		svg.append("g")
			.attr("class", "grid")
			.attr("transform", "translate(0," + height + ")")
			.call(make_x_gridlines()
				.tickSize(-height)
				.tickFormat("")
			);
		svg.append("g")
			.attr("class", "grid")
			.call(make_y_gridlines()
				.tickSize(-width)
				.tickFormat("")
			);

		// Verify string is in expected Date format, e.g.: 2019-08-18 18:00:00
		function parseISO8601(dateStringInRange) {
			var isoExp = /^\s*(\d{4})-(\d\d)-(\d\d)\s(\d{2}):(\d{2}):(\d{2})\s*$/;
			var date = new Date(NaN);
			var month = null;
			var parts = isoExp.exec(dateStringInRange);
			if (parts) {
			  month = + parts[2];
			  date.setFullYear(parts[1], month - 1, parts[3]);
			  if (month != date.getMonth() + 1) {
				date.setTime(NaN);
			  }
			  date.setHours(parts[4]);
			  date.setMinutes(parts[5]);
			  date.setSeconds(parts[6]);
			}
			console.log(' parseISO8601 returning: ', date);
			// Overloading the return since we sometimes need the hour/min value
			return [date, parts[4], parts[5]];
		}

		// Conditionally set the bar color
		function colorStatus(d) {
			if (d.job_completed === true){
				return "CornflowerBlue";
			} else if (d.job_completed === false) {
				return "Coral";
			} else {
				return "SlateGray";
			}
		}

		// Insert jsonData into our chart as colored rectangles
		svg.append("g")
			.selectAll("rect")
			.data(jsonData)
			.enter()
			.append("rect")
			.attr("class", "content")
			.attr("x", function(d){
				// Convert type string->Date, get hours and transform to decimal
				//var start = parseISO8601(d.time_started);
				//var xValue = d3.timeFormat("%X")(start).split(":");
				//var decimalHour = parseFloat(xValue[0]) + parseFloat(xValue[1]/60);
				//console.log('  -- time_started: ', d.time_started);
				//console.log('  -- start: ', start);
				//console.log('  -- xValue: ', xValue);
				//console.log('  -- decimalHour: ', decimalHour);
				//return xScale(decimalHour);
				var values = parseISO8601(d.time_started);
				var decimalHour = parseFloat(values[1]) + parseFloat(values[2]/60);
				console.log('  -- time_started: ', values[0]);
				console.log('  -- hour: ', values[1]);
				console.log('  -- min: ', values[2]);
				console.log('  -- decimalHour: ', decimalHour);
				return xScale(decimalHour);
			})
			.attr("y", function(d) {
				  var values = parseISO8601(d.time_started);
				  var start = values[0];
				  return yScale(d3.timeDay.floor(start));}
			)
			.attr("width", function(d){
				var start = parseISO8601(d.time_started);
				var stop = parseISO8601(d.time_finished);
				// Convert milliseconds->hours to match our graph interval
				return xScale((stop[0]-start[0]) / 3600000);
			})
			.attr("height", barHeight)
			.attr("rx", 5)
			.attr("ry", 5)
			.style("fill", colorStatus)
			.style("stroke", colorStatus)
			.append("svg:title")
			//.text(function(d){ return(d.time_started) + ' - ' + (d.time_finished); })
			.text(function(d) {
				var dictionary = d;
				var tmp = "";
				for (var key in dictionary) {
					if (dictionary.hasOwnProperty(key)) {
						tmp += key + ": " + dictionary[key] + '\n';
					}
				}
				return tmp;
			})

			.datum(function(d){ return Date.parse(d); });
			//.on("mouseover", function(d) {
			//	toolTip.transition()
			//		.duration(200)
			//		.style("opacity", 0.9);
			//	//toolTip.html(formatTime(d.date) + "<br/>"  + d.close)
			//	toolTip.html(
			//		function(d) {
			//			console.log('computing toolTip: ' + d.job);
			//			var dictionary = d;
			//			var tmp = "";
			//			for (var key in dictionary) {
			//				if (dictionary.hasOwnProperty(key)) {
			//					tmp += key + ": " + dictionary[key] + '\n';
			//				}
			//			}
			//			return tmp;
			//		})
			//		.style("left", (d3.event.pageX) + "px")
			//		.style("top", (d3.event.pageY - 28) + "px");
			//	})
			//.on("mouseout", function(d) {
			//	toolTip.transition()
			//		.duration(500)
			//		.style("opacity", 0);
			//});


	}

	// Expose the function for external calls
	exports.exec = exec;
})));

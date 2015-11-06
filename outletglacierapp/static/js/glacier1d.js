/*******************************************************
 * Display the extracted 1-d geometry
 *******************************************************/
$(document).ready(function() {
  // provide call back to init
  glacier1d.init();
});

var glacier1d = {};  // deal with plotting glacier1d
glacier1d.subplots = [];

glacier1d.init = function() {
  glacier1d.makeit();
  glacier1d.vizualizeit();
  glacier1d.addUI();

}

glacier1d.makeit = function(callback) {
  var formdata = $('#extractform').serializeArray();
  $('#refresh-glacier1d').button('loading')
  $.ajax({
    url: '/glacier1d',
    data: formdata,
    type: "POST",
    dataType : "json",
    success: function( json ) {
      console.log('glacier data received OK');
      $('#refresh-glacier1d').button('reset')
      glacier1d.json = json;
      glacier1d.subplots = glacier1d.GlacierChart(json);
      // if (map) {
      //   glacier1d.focusMap();
      // }
    },
    error: function( xhr, status, errorThrown ) {
      $('#refresh-glacier1d').button('reset')
      var w = window.open(null, "_self")
      w.document.open()
      w.document.write(xhr.responseText)
      w.document.close()
      // console.log( "Error: " + errorThrown );
      // console.log( "Status: " + status );
      // console.dir( xhr );
      // alert( "Error when receiving glacier1d data from server." );
    }
  });
}

glacier1d.vizualizeit = function() {
  // normally not used, vizualize currently stored glacier1d
  d3.json("/figure/glacier1d", function(error, json) {
    if (error) return console.warn(error);
    glacier1d.json = json;
    glacier1d.subplots = glacier1d.GlacierChart(json);
    // if (map) {
    //   glacier1d.focusMap();
    // }
  })
}

glacier1d.GlacierChart = function(json) {

  // the json data contains :
  // - sources
  // - views
    
  // package data with points including x, y fields
  // var newobj = {};
  // var variablelist = d3.merge(json.views.map(function(d){return d.names;}));
  // variablelist.forEach( function(nm) {
  //   json[nm] = data[nm].map(function(d, i) {
  //     return {x:data.x[i], y:d};
  //   })
  // })

  var selection = d3.select("#glacier1d").selectAll("div.view")
    .data(json.views)

  var xDomain;

  glacier1d.onbrushmove = function(brush) {
    glacier1d.subplots.forEach( function(subplot) {
      subplot.brush.extent(brush.extent())
      subplot.svg.select('g.brush').call(subplot.brush)
    })
    // shade points on the map
    if (mesh && mesh.chart) {
      // hide glacier1d out-of-focus points
      mesh.chart.refresh_after_glacier1d(brush.extent());
    }
  }

  glacier1d.onbrushend = function(brush) {
    console.log(brush.extent())
    var xdom;
    if (brush.empty()) {
      xdom = xDomain; 
    } else {
      xdom = brush.extent();
    }
    glacier1d.subplots.forEach( function(subplot) {
      subplot.x.domain(xdom);
      subplot.autoscale_y();
      subplot.refresh();
      subplot.brush.clear();
      subplot.svg.select('g.brush').call(subplot.brush)
    })

    // shade points on the map
    if (mesh && mesh.chart) {
      // hide glacier1d out-of-focus points
      mesh.chart.refresh_after_glacier1d();
    }

    // replot the map around the area of interest
    // if (map && map.chart) {
    //   glacier1d.focusMap(xdom);
    // }
  }

  // enter selection: add svg if needed
  selection.enter() 
    .append("div")
    .attr("class","view")
    .append("svg")
    .attr("width", json.width)
    .attr("height", json.height)

    .each( function(view, i) {
      glacier1d.subplots[i] = glacier1d.LineChart( {
        svgContainer : d3.select(this),
        width : json.width,
        height : json.height,
        id : view.id
      })
      // console.log(view)
    })



  // add a few functions to views
  selection
    .attr("id", function(view) {return view.id;})
    .each( function(view, i) {

      // filter source data for that view
      // console.log(json)
      // console.log(view)
      glacier1d.subplots[i]
        .data(view.names.map(function(name) { 
          return {values: json.sources[name].values.map(function(d){
            if (d.y === json.sources[name].missing_values) {
              d.y = NaN;
            }
            return d;
          }),
          id:name};
          }))
        .autoscale() // adjust x & y scales
        .xlabel(view.xlabel)
        .ylabel(view.ylabel)
        .legend()
        .refresh();

    })

  // full domain, for brush, zoom...
  xDomain = glacier1d.subplots[0].x.domain();


  // remove the svg if no views
  selection.exit()
    .remove()

  return glacier1d.subplots;
}

glacier1d.LineChart = function(params) {

  var margin = {
    left : 60,
    bottom : 25,
    right : 10,
    top : 10
  };

  // axis labels positioning
  var xlabel_offset = 40; // vertical offset
  var ylabel_offset = -45; // horizontal offset

  var svgContainer = params.svgContainer,
      width = params.width,
      height = params.height,
      // width = params.width - (margin.left+margin.right),
      // height = params.height - (margin.bottom+margin.top),
      id = params.id;

  var colors = d3.scale.category10();

  var x = d3.scale.linear()
    .range([0, width]);

  var y = d3.scale.linear()
    .range([height, 0]);

  // axes
  var xAxis = d3.svg.axis()
    .scale(x)
    .orient('bottom')
    .ticks(5)
    .tickSize(-height)


  var yAxis = d3.svg.axis()
    .scale(y)
    .orient('left')
    .ticks(5)
    .tickSize(-width)

  var lineFunction = d3.svg.line()
    .x(function(d) { return x(d.x)})
    .y(function(d) { return y(d.y)})
    .interpolate("linear")
    .defined(function(d) {console.log('isfedined?'+isNaN(d.y)); return !isNaN(d.y);})

  var brush = d3.svg.brush()
          .x(x)
          .on("brush", function() {
            glacier1d.onbrushmove(brush);})
          .on("brushend", function() {
            glacier1d.onbrushend(brush);})

  var origin = {
    x : margin.left,
    y : margin.top
  }

  // axis translation based on orientation
  // pre-enter various possible orientations
  var translate = {
    bottom : [0, height],
    left : [0, 0],
    right : [width, 0],
    top : [0, 0]
  }

  // modification of the HTML
  var svg = svgContainer.append("g")

  function resize_margins() {
    svgContainer
      .attr("width", width + (margin.left+margin.right))
      .attr("height", height + (margin.bottom+margin.top))
    svg
      .attr("transform", "translate("+[margin.left,margin.top]+")")
  }

  resize_margins();

  // var event_listener = svg
  // .append("rect")
  //   .attr("width", width)
  //   .attr("height", height)
  //   .style("opacity", 1e-6) // invisible
  //   .style("fill", "000")
  //   // .on("dblclick", function() {
  //   // });

  var lines = svg
  .append('g')
  .selectAll('path.line')

  var xAxisSvg = svg.append("g")
  .attr("class", "x axis")
  .attr("transform", "translate("+ translate[xAxis.orient()] + ")")

  var yAxisSvg = svg.append("g")
  .attr("class", "y axis")
  .attr("transform", "translate("+ translate[yAxis.orient()] + ")")

  var legendSvg = svg.append("g")
    .attr("class","legend")
    .attr("transform","translate("+[0.05*width,0.1*height]+")")

  var xlabel = svg.append("text")      // text label for the x axis
        .attr("class", "x axis")
        .attr("x", width/2 )
        .attr("y", height+xlabel_offset)
        .style("text-anchor", "middle")
        .text("");

  var ylabel = svg.append("text")      // text label for the x axis
        .attr("class", "y axis")
        .attr("transform","translate("+[0+ylabel_offset, height/2]+")rotate(-90)")
        .style("text-anchor", "middle")
        .text("");

  var brushSvg = svg.append("g")
    .attr("class","x brush")

  svg
    .append("defs")
    .append('clipPath')
    .attr('id', "clip-path-"+id)
    .append("rect")
    .attr("width",width)
    .attr("height",height)

  var data = [];

  var chart = {};

  // add a zero line
  var zeroline = svg.append('line')
    .style('stroke-width',1)
    .style('stroke','black')

  chart.refresh = function() {

    // autoscale_y(); // 
    zeroline
      .attr('x1', x.range()[0])
      .attr('x2', x.range()[1])
      .attr('y1',y(0))
      .attr('y2',y(0))

    lines = lines.data(data)

    lines.enter()
    .append('path')
    .classed('line', true)
    .attr('clip-path','url(#clip-path-'+id+')')
    .style("stroke", function(d,i){return colors(i)})

    lines
    .attr("data-legend",function(line) {return line.id;})
    .attr('d', function(line) {return lineFunction(line.values)})

    lines.exit()
    .remove()

    xAxisSvg.call(xAxis)
    yAxisSvg.call(yAxis)
    legendSvg.call(d3.legend)

    brushSvg
    .call(brush)
    .selectAll('rect') // since there is no y-variable, need to indicate size manually
    .attr("height", height)
    .attr("y", 0)

    return chart;
  }

  // GETTER SETTER

  chart.data = function(values) {
    if (!arguments.length) return data;
    data = values;

    return chart;
  };

  // autoscale axes
  function getrange(field) {
    return d3.extent(d3.merge(data.map(function(line) { 
      return line.values.map(function(pt) {
        return pt[field]; 
      })
    })))
  }
  chart.getrange = getrange; 

  chart.autoscale_y = function() {

    // only select data that falls in the x domain
    var xdom = x.domain();

    var ydom = d3.extent(d3.merge(data.map(function(line) { 
      return line.values.filter( function(pt) {
          return (pt.x >= xdom[0]) && (pt.x <= xdom[1]);
      })
      .map(function(pt) { return pt.y; })
    })))

    y.domain(ydom).nice();
    return chart;
  };
  chart.autoscale_x = function() {
    var xrange = getrange('x')
    // x.domain(xrange).nice();
    x.domain(xrange);
    brush.x(x);

    return chart;
  };
  chart.autoscale = function() {
    return chart.autoscale_x().autoscale_y();
  };

  chart.xlabel = function(lab) {
    // change the margin?
    var inc = 0;
    if ((lab !== '') && (xlabel.text() === '')) inc = 15;
    if ((lab === '') && (xlabel.text() !== '')) inc = -15;
    margin.bottom += inc; // update bottom margin
    resize_margins();
    xlabel.text(lab)
    return chart;
  }
  chart.ylabel = function(lab) {
    // add label
    ylabel.text(lab)
    return chart;
  }
  chart.legend = function() {
    // add legend
    return chart;
  }
  chart.margin = function(_) {
    if (!arguments.length) return margin;
    for (field in _) {
      margin[field] = _[field];
    }
    resize_margins();
  }

  // limit extent of panning for the current zoom level
  chart.panLimit = function(panExtent) {
    zoom.translate( glacier1d.panLimit(x, y, zoom, panExtent) )
    return chart; 
  }

  // Access other chart properties from outside
  chart.x = x;
  chart.y = y;
  chart.brush = brush;
  chart.svg = svg;

  return chart;
}

// add user interface
glacier1d.addUI = function() {
  // $('#extractform select').on('change', function() {
  //   glacier1d.makeit();
  // })
  $('#refresh-glacier1d').on('click', function() {
    glacier1d.makeit();
  })
}

  // download map corresponding to glacier1d (full domain)
glacier1d.focusMap = function(xdom) {
  var xcoord, ycoord, xrange, yrange;

  function filter(pt) {
    if (!xdom) return true;
    return (pt.x >= xdom[0]) && (pt.x <= xdom[1]);
  };

  xcoord = glacier1d.json.sources['x_coord']
    .filter(filter)
    .map(function(pt) {return pt.y})

  ycoord = glacier1d.json.sources['y_coord']
    .filter(filter)
    .map(function(pt) {return pt.y})

  xrange = d3.extent(xcoord)
  yrange = d3.extent(ycoord)

  var m = 50; // margin, in km
  map.coordsCtrl.setCoords([xrange[0]-m, xrange[1]+m, yrange[0]-m, yrange[1]+m])
  map.get_and_update_data();
}

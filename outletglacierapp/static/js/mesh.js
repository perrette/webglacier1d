/*******************************************************************
 * Display mesh and glaciers
 *******************************************************************/
$(document).ready(function() {
  // provide call back to init
  map.init( function() {
    map.get_and_update_data(); 
    mesh.init();
    map.dependencies.push(mesh.chart)
    var lines = mesh.meshGeneratorChart();
    map.dependencies.push(lines)
  });
});

var mesh = {}; // deal with mesh

mesh.init = function() {
  mesh.chart = mesh.MeshChart(map.chart.svg, map.chart.x, map.chart.y, {zoom:map.chart.zoom});
  $.getJSON('/mesh', function(json) {
    console.log('received mesh data')
    mesh.chart.data(json.mesh)
      .call()
  })
  mesh.add_UI();
}

mesh.MeshChart = function(svg, x, y, options) {

  // plot the mesh onto the map chart
  var lineFunction = d3.svg.line()
    .x(function(d) { return x(d.x)})
    .y(function(d) { return y(d.y)})
    .interpolate("linear");

  var svg = svg
    .append('g')
    .attr('class','mesh')

  var flowlines = svg
    .append('g')
    .attr('class','line flowline')
    .selectAll('path')

  var sections = svg
    .append('g')
    .attr('class','line section')
    .selectAll('path')

  var nodes = svg
    .append('g')
    .attr('class','node')
    .selectAll('circle')

  var data = [[]]; // list of sections

  function chart(selection) {

    // make sure the data is attached
    // lines = lines.data(d3.pairs(data));
    sections = sections.data(data); 
    flowlines = flowlines.data(d3.transpose(data)); 
    nodes = nodes.data(d3.merge(data)); // flat array of nodes

    // lines
    flowlines.enter()
      .append('path')
      .attr('clip-path','url(#canvas-clip)')
      
    flowlines
      .attr('d', lineFunction)

    flowlines.exit()
      .remove()

    sections.enter()
      .append('path')
      .attr('clip-path','url(#canvas-clip)')
      
    sections
      .attr('d', lineFunction)

    sections.exit()
      .remove()

    // nodes
    nodes.enter()
      .append('circle')
      .attr('clip-path','url(#canvas-clip)')

    nodes
      .attr("cx", function(d) {return x(d.x);})
      .attr("cy", function(d) {return y(d.y);})
      .attr("r", 2)

    nodes.exit()
      .remove()

    chart.refresh_after_glacier1d();

    return chart;
  };

  // connect to external events


  // refresh based on glacier1d selection
  chart.refresh_after_glacier1d = function(xdom) {
    if (glacier1d && glacier1d.subplots && glacier1d.subplots.length) {
      var xdom = xdom || glacier1d.subplots[0].x.domain();
      nodes.classed("shaded", function(d, i) {
        return (d.s < xdom[0]) || (d.s > xdom[1]);
      }) 
      sections.classed("shaded", function(d, i) {
        return (d[0].s < xdom[0]) || (d[0].s > xdom[1]);
      }) 
    }
  }
    
  // Re-draw on zoom
  if (options.zoom) {
    options.zoom.on('zoom.mesh', function() {
      if (d3.event.defaultPrevented) return;
      chart();
    })
  }

  // delete the chart
  function remove() {
    data = [];
    chart();
    if (options.zoom) {
      options.zoom.on('zoom.mesh', null)
    }
  }

  // getter / setters

  // attach data from outside, or access it
  chart.data = function(values) {
    if (!arguments.length) return data;
    data = values;
    return chart;
  };

  chart.remove = remove;

  return chart;

}
mesh.remesh = function() {
  console.log("OLD REMESH CLICKED")
  var form = $("#mesh-form").serializeArray();
  console.log(form)
  $('#remesh-btn').button('loading')
  $.post('/mesh', form, function(json) {
    $('#remesh-btn').button('reset')
    mesh.chart.data(json.mesh) // update mesh
    .call()
    glacier1d.makeit();
  })
}

// this function extract outline from an existing mesh
mesh.extractOutline = function() {
  var form = $("#mesh-form").serializeArray();
  console.log(form)
  $.get('/meshoutline', form, function(json) {
    json.lines.forEach(function(line,i){
      drawing.linecharts[i].id(line.id);
      drawing.linecharts[i].data(line.values)();
    })
  })
}

mesh.add_UI = function() {
  // $("#remesh").on("click", mesh.remesh)
    
  $("#meshoutline-btn").on("click", function(event) {
    mesh.extractOutline()
    console.log("extract outline")
    event.preventDefault();
  })

  $("#remesh-btn").on("click", function(event) {
    mesh.remesh()
    console.log("submit form")
    event.preventDefault();
  })

  // pressKey r
  $('body').on("keydown", function(event) {
    console.log(event)
    if (event.keyCode === 82 && ! event.ctrlKey) {
      mesh.remesh()
    }
  })

}

mesh.meshGeneratorChart = function() {

  drawing.linecharts = [];

  // add mesh generator
  $.getJSON('/lines', function(json) {
    console.log('received lines data')

    json.lines.forEach(function(line) {
      var linechart = drawing.drawLine(
        {x: map.chart.x, 
          y: map.chart.y, 
          on: map.chart.on, // register event
          svg: map.chart.svg,
          id: line.id,
          data: line.values
        }).call();

        // remove appending point on drawing
        map.chart.on('click.drawing', null)

        drawing.linecharts.push(linechart);
    })
  })

  // refresh chart (e.g. zoom, new map...)
  function chart() {
    drawing.linecharts.forEach( function(linechart) {
      linechart();
    })
  }

  //chart.linecharts = drawing.linecharts;

  // replace remesh by also posting lines
  var remesh_wo_postline = mesh.remesh;

  mesh.remesh = function() {
    console.log("NEW REMESH CLICKED")
    drawing.postLinesToServer(remesh_wo_postline)
  }

  return chart;
}

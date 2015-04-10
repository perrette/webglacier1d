/***********************
 * Draw lines on graphic
 ***********************/
var drawing = {};

function initialize() {
  console.log('start drawing')
  // provide call back to init
  map.init( function() {
    map.get_and_update_data(); 
    drawing.makeLinesChart();
    drawing.addToolkit();
    map.dependencies.push( drawing.updateLines)
  });
}

drawing.drawLine = function(args) {
  // arguments contains: 
  // - x, y: axis scales 
  // - on: to register event (zoom, click)
  // - svg: d3 selection, element to which to append the points
  // - id: id of the drawing area to add
  // - $toolkit: parent for the toolkit, append the buttons for interactive use
  //

  // define arguments in the local workspace
  var x = args.x;
  var y = args.y;
  var on = args.on;
  var svg = args.svg;
  var $toolkitContainer = args.$toolkitContainer;
  var id = args.id;
  var data = args.data || [];

  var drag = d3.behavior.drag()
              .origin(function(d) { return d; })
              // .on("dragstart", function() {d3.event.stopPropagation()})
              .on('drag', movePoint)
              .on('dragend', ondragend);

  // attach events to canvas
  on('click.drawing', appendPoint)

  // Re-draw on zoom
  on('zoom.drawing'+id, function() {
    if (d3.event.defaultPrevented) return;
    chart()
  })

  var drawingArea = svg
    .append('g')
    .classed('drawing',true)
    .classed(id, true)

  var linksArea = drawingArea
    .append('g')
    .attr('class','links');
     
  var nodesArea = drawingArea
    .append('g')
    .attr('class','nodes')

  var linkFunction = d3.svg.line()
    .x(function(d) { return x(d.x)})
    .y(function(d) { return y(d.y)})
    .interpolate("linear");

  var nodes = nodesArea.selectAll('circles .node')

  var links = linksArea.selectAll('path .link')

  function chart(selection) {

    // make sure the data is attached
    nodes = nodes.data(data);
    links = links.data(d3.pairs(data));

    // add linear coordinate, can be useful
    // TODO: make a separate refresh function
    // on zoom to avoid redrawing everything
    data = drawing.addLinearCoord(data);

    // add a values field to data
    data = data.map(function(d) {
      d.value = map.chart.get_value(d.x, d.y);
      return d;
    })

    // nodes
    nodes.enter()
      .append('circle')
      .attr('class','node')
      .attr('clip-path','url(#canvas-clip)')
      .on('click', deletePoint)
      .call(drag);

    nodes
      .attr("cx", function(d) {return x(d.x);})
      .attr("cy", function(d) {return y(d.y);})
      .attr("r", 5)

    nodes.exit()
      .remove()

    // links
    links.enter()
      .append('path')
      .attr('class','link')
      .attr('d', linkFunction)
      .attr('clip-path','url(#canvas-clip)')
      .on('mouseup', insertPoint)
      
    links
      .attr('d', linkFunction)

    links.exit()
      .remove()

    // make sure the data are reflected in the HTML field, if any
    if ($toolkit) {
      $textfield.val(format_data())
      // textfield.attr('rows',d3.min([10,data.length]))
      $textfield.attr('rows',10)
      $resamplehtml.val(data.length)
    };

    // make a plot to reflect values on the map
    if ($toolkit) {
      // select a subset of data that fits on the map
      var domx = x.domain();
      var domy = y.domain();
      var datazoom = data.filter(function(d){
        return map.isNumber(d.value)&d.x>domx[0] & d.x<domx[1] & d.y>domy[0] & d.y<domy[1];
      })
      snippetchart.data(datazoom)
        (); // update time series
    }

    return chart;
  };

  // events
  function appendPoint() {
    if (d3.event.defaultPrevented) return;
    if (!chart.selected()) {chart.select(); return;};
    var mouse = d3.mouse(this);
    var point = {x: x.invert(mouse[0]),
                 y: y.invert(mouse[1])};
    // console.log(point)
    data.push(point);
    saveData("append point");
    chart();
  };

  function insertPoint(link, i) {
    if (!chart.selected()) {chart.select(); return;};
    var mouse = d3.mouse(this);
    var point = {x: x.invert(mouse[0]),
                 y: y.invert(mouse[1])};
    // console.log(point)
    data.splice(i+1, 0, point); // insert point in data
    saveData('insert point')
    chart();
  };

  function deletePoint(point, i) {
    if (d3.event.defaultPrevented) return;
    if (!chart.selected()) {chart.select(); return;};
    data.splice(i, 1); // deleted
    saveData('delete point')
    chart();
  }

  function ondragend(d,i) {
    saveData('move point');
  }
  function movePoint(d,i) {
    if (d3.event.defaultPrevented) return;
    if (!chart.selected()) {chart.select(); return;};
    var mouse = d3.mouse(this);
    data[i] = {x: x.invert(mouse[0]), y:y.invert(mouse[1])};
    chart(); // update chart
  }

  // clear line
  function clear() {
    if (!data.length) return;
    data = [];
    saveData('clear data')
    chart(); // remove points
  }


  // attach data from outside, or access it
  chart.data = function(values) {
    if (!arguments.length) return data;
    data = values;
    saveData('update data')
    return chart;
  };

  // remove the plot, including DOM element
  // call drawing.removeLine instead to benefit from Undo
  chart.remove = function() {
    // clear();
    data = [];
    clearStacks();
    drawingArea.remove(); // remove drawing area from the DOM

    if ($toolkit) {
      $toolkit.remove();
    };

  }

  // // remove on press del
  // d3.select("body").on("keydown."+chart.id, function() {
  //   if (!chart.selected()) {return;};
  //   console.log(d3.event.keyCode)
  //   if (d3.event.keyCode === 46) {
  //     // chart.remove();
  //     drawing.removeLine(chart.id);
  //   }
  // })


  /********************************
   * also add a few buttons
   * ******************************/

  // undo / redo
  var undoStack = []; 
  var redoStack = []; 
  function saveData(action) {
    console.log(action) 
    undoStack.push([action,data.concat()]); // copy
  }
  function undo() {
    if (!undoStack.length) return;
    var tmp = undoStack.pop();
    redoStack.push(tmp)
    console.log("undo "+tmp[0])
    if (!undoStack.length) {
      data = [];
    } else {
      var tmp = undoStack[undoStack.length-1];
      data = tmp[1];
    }
    chart();
    chart.select();
  }
  function redo() {
    if (!redoStack.length) return;
    var tmp = redoStack.pop();
    console.log("redo "+tmp[0])
    undoStack.push(tmp);
    data = tmp[1];
    chart();
    chart.select();
  }
  function clearStacks() {
    undoStack = [];
    redoStack = [];
  };

  var $toolkit;

  if ($toolkitContainer) {

    // append a toolkit div as container
    $toolkit = $('<tr><td><div> </div></td></tr>')
      .attr("class",'toolkit '+id)
      // .attr("id",'toolkit-'+id)
      .appendTo($toolkitContainer);

    // display ID
    var $id = $('<input></input>')
    .attr("class","btn")
    .attr("size",4)
    .val(id)
    .appendTo($toolkit)
    .on('change', function() {
      chart.id($id.val()); // update chart ID
    })

    // button template
    var $btn = $('<input></input>')
    .attr("type","button")
    .attr("class", "btn")

    // undo
    $btn.clone()
      .val("Undo")
      .appendTo($toolkit)
      .click(undo)

    // undo
    $btn.clone()
      .val("Redo")
      .appendTo($toolkit)
      .click(redo)

    // clear points
    $btn.clone()
      .val("Clear")
      .appendTo($toolkit)
      .click(function() {
        clear()
      })

    // Resample
    var $resamplebtn = $btn.clone()
      .addClass("btn")
      .val("Resample")
      .appendTo($toolkit)
      .click(function() {
        var n = parseInt($resamplehtml.val());
        data = drawing.resample(data, n);
        saveData('resample data')
        chart();
      })

    // add text
    var $resamplehtml = $('<input></input>')
    .attr("type","text")
    .attr("size","3")
    .val("50")
    .appendTo($toolkit)
    .change(function(){$resamplebtn.trigger('click')})


    // add toggle vizualization area
    // for points and figure
    $btn.clone()
      // .addClass("btn-success")
      .addClass("btn")
      .addClass("btn-danger")
      .val("...")
      .appendTo($toolkit)
      .click(function() {
        // $textfield.toggle();
        if (chart.selected()) {
          chart.unselect();
        } else {
          chart.select();
        };
      });

    // clear and remove from DOM
    $btn.clone()
      .addClass("btn")
      .addClass("btn-danger")
      .val("X")
      .appendTo($toolkit)
      .click(function() {
        // r = confirm("Remove this line? This action cannot be cancelled.");
        // if (r === true) {
          // chart.remove();
          drawing.removeLine(chart.id());
        // }
      })


    // a view area with more info such as text area for points and inset plot
    $('<br>')
      .appendTo($toolkit)

    // var viewid = "view-"+id;
    var viewDiv = $('<div> <textarea> </textarea> <svg> </svg> </div>')
        .appendTo($toolkit)

    // write the data to a text input element
    // var $textfield = $('#'+viewid+' textarea')
    var $textfield = $('.toolkit.'+id+' textarea')
      .attr('rows',data.length)
      .attr('cols',14)
      .attr('margin',5)

    $textfield
      .on('change',function(event) {
        var newdata = parse_text($textfield.val()); // update data
        chart.data(newdata)();
        });

    function format_data() {
      // get data in a text form appropriate to fill the textarea input
      var text = "";
      var fmt = d3.format('.1f');
      //var fmt = d3.format();
      data.forEach(function(d) {
        text += fmt(d.x)+";"+fmt(d.y)+"\n"; 
      })
      return text;
    }

    // http://stackoverflow.com/questions/1418050/string-strip-for-javascript
    var strip = function(str) 
    {
      return str.replace(/^\s+|\s+$/g, '');
    };

    function parse_text(text) {
      text = strip(text);
      var newdata = text.split('\n').map(function(d) {
        var newd = d.split(';').map(parseFloat);
        return {x:newd[0], y:newd[1]};
      })
      return newdata;
    }

    /***************************************
     * Also add an inset plot of the line
     ****************************************/
    var plotsnippet = d3.select('.toolkit.'+id+' svg')
    // .attr('id','plotsnippet-'+args.id)
    // .appendTo(args.$toolkit);

    var snippetchart = drawing.linePlot( plotsnippet );

  } else {
    var viewDiv = $('<div></div>'); // dummy
  };

  /***********
  * control visibility
  * **********/
  chart.unselect = function() {
    // $textfield.hide();
    viewDiv.hide();
    selected = false;
    // make it less visible
    nodes.each(function(){d3.select(this).classed('shaded',true)})
    links.each(function(){d3.select(this).classed('shaded',true)})
  };

  chart.select = function() {
    // unselect all other plots
    drawing.linecharts.forEach(function(d) { 
      d.unselect(); 
    })
    // $textfield.show();
    // plotsnippet.show();
    viewDiv.show();
    selected = true;
    links.each(function(){d3.select(this).classed('shaded',false)})
    nodes.each(function(){d3.select(this).classed('shaded',false)})

    // associate click events to this graph
    on('click.drawing', appendPoint)
  };

  var selected = true;

  // getter / setter a la d3, for convenience
  chart.selected = function(value) {
    if (!arguments.length) {
      // return ($textfield.is(':visible')); 
      return selected;
    }
    if (value) {
      chart.select();
    } else {
      chart.unselect();
    }
  };

  chart.id = function(value) {
    if (!arguments.length) return id;
    d3.selectAll('.'+id)
      .classed(id, false)
      .classed(value, true) // update graphical elements's id
    id = value; // identify line in the array.
    return chart;
  }

  return chart;

};

/*******************************************
 *
 * Basic operations on lines
 *
 ********************************************/
// add a linear coordinate to the data (km)
drawing.addLinearCoord = function(dat) {
  var s = 0;
  var d0; 
  dat = dat.map(function(d, i) {
    if (i!==0) {
      var distance = Math.sqrt(Math.pow(d.x-d0.x, 2) + Math.pow(d.y-d0.y, 2)); // distance
      s += distance; 
    };
    d0 = d; // for next iteration

    d.s = s;
    return d;
  });
  return dat;
};

// resample line data
drawing.resample = function(dat, npoints) {

  if (dat.length < 2) {
    return dat;
  }

  var n = npoints || 100; // number of points to resample

  // add a linear coordinate to the data
  dat = drawing.addLinearCoord(dat);

  // construct a linear scale with d3.scale
  var xrange = [], yrange = [], srange = [];
  dat.forEach(function(d, i) {
    xrange.push(d.x)
    yrange.push(d.y)
    srange.push(d.s)
  })

  var xscale = d3.scale.linear()
  .domain(srange)
  .range(xrange)

  var yscale = d3.scale.linear()
  .domain(srange)
  .range(yrange)

  var total_length = dat[dat.length-1].s;
  var r = total_length/(n-1);

  newdata = d3.range(n).map(function(i) {
    var s = i*r; // between 0 and total_length
    return {
      s: s,
      x: xscale(s),
      y: yscale(s),
    }
  })

  return newdata;
};

/*******************************************
 *
 * Simple insert plot
 *
 ********************************************/
drawing.linePlot = function(container) {

  var total_width = 300,
      total_height = 200;

  var margin = {
    left : 50,
    bottom : 50,
    right : 20,
    top : 20
  };

  var interior = {
    left : margin.left,
    bottom : total_height-margin.top,
    right : total_width-margin.left,
    top : margin.top
  }

  var origin = {
    x : interior.left,
    y : interior.top
  }


  var width = interior.right - interior.left;
  var height = interior.bottom - interior.top;

  var data = {};

  var linkFunction = d3.svg.line()
    .x(function(d) { return x(d.s)})
    .y(function(d) { return y(d.value)})
    .interpolate("linear");

  var x = d3.scale.linear()
          .range([0, width]);

  var y = d3.scale.linear()
          .range([height, 0]);

  var xAxis = d3.svg.axis()
          .scale(x)
          .orient("bottom")
          .ticks(5)

  var yAxis = d3.svg.axis()
          .scale(y)
          .orient("left")
          .ticks(5)

  var zoom = d3.behavior.zoom()
          .x(x)
          .y(y)
          .on("zoom", onzoom);

  function onzoom() {
  };

  var svg = container
    .attr("width", total_width)
    .attr("height", total_height)
    .append('g')
    .attr("transform","translate("+origin.x+","+origin.y+")")
    .attr('class','inset')
    .attr("width", width)
    .attr("height", height)

  var linksArea = svg
    .append('g')
    .attr('class','links');
     
  var nodesArea = svg
    .append('g')
    .attr('class','nodes')

  var labelsArea = svg
    .append('g')
    .attr('class','labels')

  var yAxisSvg = svg.append("g")
          .attr("class", "y axis")
          .call(yAxis)

  var xAxisSvg = svg.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0, "+ height + ")")
          .call(xAxis)

  var labels = labelsArea.selectAll('text .label')
  var nodes = nodesArea.selectAll('circles .point')
  var links = linksArea.selectAll('path .line')

  function chart(selection) {

    // make sure the data is attached
    nodes = nodes.data(data);
    labels = labels.data(data);
    links = links.data(d3.pairs(data));

    // update x and y ranges
    if (data.length > 0) {
      x.domain([data[0].s, data[data.length-1].s])
      y.domain(d3.extent(data.map(function(d){return d.value;})))
      xAxis.scale(x);
      yAxis.scale(y);
    };

    // update axes
    xAxisSvg.call(xAxis)
    yAxisSvg.call(yAxis)


    // // label
    // labels.enter()
    //   .append('text')
    //   .attr('class', 'label')
    //   .attr("hidden", true)
    //
    // labels
    //   .attr("x", function(d) {return d.s;})
    //   .attr("y", function(d) {return d.value;})
    //
    // labels.exit()
    //   .remove()

    // nodes
    nodes.enter()
      .append('circle')
      .attr('class','point')
      .att

    nodes
      .attr("cx", function(d) {return x(d.s);})
      .attr("cy", function(d) {return y(d.value);})
      .attr("r", 2)
      // .on('mouseover', )

    nodes.exit()
      .remove()

    // links
    links.enter()
      .append('path')
      .attr('class','line')
      .attr('d', linkFunction)
      
    links
      .attr('d', linkFunction)

    links.exit()
      .remove()

    return chart;
  };

  /**************************
   * getter / setter methods
   **************************/

  chart.data = function(value) {
    if (!arguments.length) return data;
    data = value;

    return chart;
  };

  return chart;
};

/********************************************
 * Plot lines and extract data along lines
 ********************************************/

drawing.makeLinesChart = function() {
        
  // attach to the top object
  drawing.id = 0;
  drawing.linecharts = []; // store all line charts

  // add DOM element containing the drawing
  drawing_area = d3.select('#canvas-origin')
  .append('g')
  .attr('id','drawing-area');

  // toolkits = d3.selectAll('.toolkit')

  // refresh all charts based on linecharts
  function refresh() {
  };

  function newLine(id, data) {
    // prepare a first chart

    var c = map.chart; // map chart

    // add a div for the toolkits
    var linechart = drawing.drawLine(
      {x: c.x, 
       y: c.y, 
       on: c.on, // register event
       svg: drawing_area,
       id: id || "ID"+drawing.id,
       $toolkitContainer: $("#drawing-single-tools"),
       data: data || []
       }).call();

    // "hide" all other lines
    drawing.linecharts.forEach(function(linechart){linechart.unselect()});
    linechart.select();

    // add to the list of charts
    drawing.linecharts.push( linechart );
    drawing.id++; // update line id

    return linechart;
  }

  drawing.newLine = newLine;

  function newFlowLine() {
    alert("Click on the map to choose a starting point.")
    map.chart.on("click.drawing", function() {
      var mouse = d3.mouse(this);

      // serialize flowline form
      var data = $('#flowline-form').serializeArray();
      var point = { 
        'x':map.chart.x.invert(mouse[0]),
        'y':map.chart.y.invert(mouse[1])
        }
      data.push({'name':'x', 'value':point.x})
      data.push({'name':'y', 'value':point.y})

      // only one try !
      map.chart.on("click.drawing", null)

      // map a request to server to start a flowline
      $.ajax({
        url: '/flowline',
        data: data,
        type: "GET",
        dataType : "json",
        success: function( json ) {
          console.log('flowline OK');
          linechart = newLine() // add normal line
            .data(json.line)
            .call();
        },
        error: function( xhr, status, errorThrown ) {
          var w = window.open(null, "_self")
          w.document.write(xhr.responseText)
          w.document.close()
          console.log( "Error: " + errorThrown );
          console.log( "Status: " + status );
          console.dir( xhr );
          alert( "Error when computing flowline." );
        }
      });
    })
  };

  drawing.newFlowLine = newFlowLine;


  var undoStack = []; 
  var redoStack = []; 
  function saveLines() {
    undoStack.push(drawing.getLines());
  }

  drawing.removeLines = function() {
    var ids = drawing.linecharts.map(function(d) {return d.id();})
    if (!ids.length) return;
    var r = confirm("This will delete all lines drawn so far, continue?");
    if (r === true) {
      ids.forEach(function(id) {drawing.removeLine(id);})
    }
  }

  drawing.removeLine = function(id, donotsave) {
    id = id || drawing.linecharts[drawing.linecharts.length-1].id(); // last ID by default
    var chart;
    // remove from linecharts
    for (var i=0; i<drawing.linecharts.length; i++) {
      chart = drawing.linecharts[i];
      if (chart.id() === id) {
        drawing.linecharts.splice(i, 1);
        break;
      }
    };
    
    if (!donotsave) {
      saveLines();
    }
    chart.remove();
    refresh();
  }

  function redo() {
    if (!redoStack.length) return;
    var lines = redoStack.pop(); // id, data
    undoStack.push(lines);
    refresh();
  }
  function undo() {
    if (!undoStack.length) return;
    var lines = undoStack.pop(); // id, data
    redoStack.push(lines);
    refresh();
  };

  drawing.upload = function(evt) {
    // http://www.html5rocks.com/en/tutorials/file/dndfiles/
    var files = evt.target.files; // FileList object
    // Loop through the FileList
    for (var i = 0, f; f = files[i]; i++) {
      var reader = new FileReader();
      // Load the file content to HTML
      reader.onload = function(e) {
        var lines = JSON.parse(e.target.result);
        addLines(lines);
      }
      // Read in the file as text
      reader.readAsText(f)
    }
    // Clear upload field
    $('#upload-lines').val("")  // clear
  }


  /**************************************************
   * Retrieve data from plot
   * ************************************************/

  function addLines(lines) {
    for (var j=0; j<lines.length;j++) {
      // create new line
      var linechart = newLine(lines[j].id)
      // attach data
      linechart
      .data(lines[j].values)
      // refresh
      linechart(); 
    }
  }

  drawing.addLines = addLines;

    // Get lines from server
    drawing.getLinesFromServer();

    // update line
    drawing.updateLines = function() {
      for (var i=0; i<drawing.linecharts.length; i++) {
        drawing.linecharts[i].call(); // update: by convention, call to refresh
      }
    }

    return drawing;
};

// Extract lines from the charts
drawing.getLines = function(charts) {

  if (drawing.linecharts.length == 0) {
    return [];
  }

  charts = charts || drawing.linecharts;
  return charts.map(function(chart) {
    return {
    id:chart.id(), 
    values:chart.data().map(function(point) {
      return {x:point.x, y:point.y};
    })};
  });
}

drawing.getLinesByID = function(id) {
  var lines = drawing.getLines().filter(function(d) {
    return d.id.toLowerCase() === id;
  })
  return lines;
}

drawing.updateID = function(oldid, newid) {
  drawing.linecharts
  .filter(function(chart) {
    return chart.id() === oldid;
  })
  .forEach(function(chart) {
    chart.id(newid);
  })
}

/**************************************************
* Server Requests Interaction
* ************************************************/

drawing.meshglacier = function() {

  var lines = drawing.getLines();
  if (lines.length !== 3) {
    alert("Need 3 lines to mesh a glacier")
    return;
  }
  var lefts = drawing.getLinesByID('left');
  var rights = drawing.getLinesByID('right');
  var middles = drawing.getLinesByID('middle');

  if (middles.length !== 1 || lefts.length !== 1 || rights.length !== 1) {
    r = confirm("Labels 'middle', 'left', 'right' not found: assume that order?")
    if (!r) { 
      return; 
    }
    // update labels
    drawing.updateID(lines[0].id, 'middle')
    drawing.updateID(lines[1].id, 'left')
    drawing.updateID(lines[2].id, 'right')
  }

  // post lines to server and wait for callback
  drawing.postLinesToServer(function() {
    var form = $("#mesh-form").serializeArray();
    console.log('meshform')
    console.log(form)
    $.post('/mesh', form, function(json) {
      console.log('mesh ok. fetch it')
        console.log(json)
        window.open('/viewmesh', '_self') 
    })
  })
}

drawing.downloadLines = function() {
    // download line data as CSV
    // // prepare json data to download
    // var json = []; 
    // drawing.linecharts.forEach(function(linechart) {
    //   json.push({
    //     // 'values':linechart.data().map(function(d) {return [d.x, d.y];}),
    //     'values':linechart.data().map(function(d) {return {'x':d.x, 'y':d.y};}),
    //     'id':linechart.id()
    //     });
    // });
    json = drawing.getLines()


    // download
    // http://stackoverflow.com/questions/17836273/export-javascript-data-to-csv-file-without-server-interaction
    var a         = document.createElement('a');
    a.href        = 'data:attachment/json,' + JSON.stringify(json);
    a.target      = '_blank';
    a.download    = 'linesCoordinates.json';
    document.body.appendChild(a);
    a.click();
}

drawing.linesURL = '/lines';

drawing.getLinesFromServer = function() {
  $.getJSON(drawing.linesURL, function(json) { drawing.addLines(json.lines) })
}

drawing.postLinesToServer = function(success) {
  console.log("===>>>> post lines to server")
  console.log(drawing)
  console.log(drawing.getLines)
  var data = drawing.getLines();
  // save lines on validation
  $.ajax({
    url: drawing.linesURL,
    data: JSON.stringify(data),
    type: "POST",
    // dataType : "json",
    contentType:'application/json',
    accepts : ["text/html","application/json"], // so that html is also accepted as a response
    // contentType:'text/html',
    success: success,
    error: function( xhr, status, errorThrown ) {
      var w = window.open(null, "_self")
      w.document.write(xhr.responseText)
      w.document.close()
      console.log( "Error: " + errorThrown );
      console.log( "Status: " + status );
      console.dir( xhr );
      alert( "Error when saving lines to server." );
    }
  });
  // console.log(data)
  // $.post('/lines', JSON.stringify(data), success);
}
    

drawing.addToolkit = function() {

  // add button to interact with lines
  toolkit = {};

  // Info text above toolkit
  var $infotext = $("#infotext")
  var $btn;

  // add a new line
  $("#new-line")
  .click(function() {
    drawing.newLine(); // add new line to draw
  })
  .on("mouseover", function() {
    $infotext.text("Add new drawline")
  })
  .on("mouseout", function() {
    $infotext.text("");
  })

  var $newflowline = $("#new-flowline")
  .click(function() {
    drawing.newFlowLine(); // add new line to draw
  })
  .on("mouseover", function() {
    $infotext.text("Add new flowline")
  })
  .on("mouseout", function() {
    $infotext.text("");
  })

  // clear lines
  $("#remove-lines")
  .click(function() {
    drawing.removeLines();
  })
  .on("mouseover", function() {
    $infotext.text("Remove all lines")
  })
  .on("mouseout", function() {
    $infotext.text("");
  })

  // $('#prev')
  //   .on('click',undo)
  //   .on("mouseover", function() {
  //     $infotext.text("Previous chart")
  //   })
  //   .on("mouseout", function() {
  //     $infotext.text("");
  //   })
  //
  // $('#next')
  //   .on('click',redo)
  //   .on("mouseover", function() {
  //     $infotext.text("Next chart")
  //   })
  //   .on("mouseout", function() {
  //     $infotext.text("");
  //   })
    
  // download coordinates for all lines
  $("#download-lines")
  .on('click', drawing.downloadLines)  
  .on("mouseover", function() {
    $infotext.text("Download line coordinates")
  })
  .on("mouseout", function() {
    $infotext.text("");
  })

  // Upload files
  var $upload = $('#upload-lines')
  .on('change', drawing.upload) 
  .on("mouseover", function() {
    $infotext.text("Upload line coordinates")
  })
  .on("mouseout", function() {
    $infotext.text("");
  })
  // save lines to server
  $("#save-lines")
  .on('click', function() {
    drawing.postLinesToServer();
  })
  .on("mouseover", function() {
    $infotext.text("Save lines to server: persist on reload")
  })
  .on("mouseout", function() {
    $infotext.text("");
  })

  $("#googlemap")
    .on('click', function() {
      console.log('click on googlemap')
      drawing.postLinesToServer(); // commit lines before going to googlemap
    })

  var $mesh = $('#mesh-glacier')
    .on("click", drawing.meshglacier)
    .on("mouseover", function() {
      $infotext.text("Save lines & mesh glacier domain")
    })
    .on("mouseout", function() {
      $infotext.text("");
    })
}

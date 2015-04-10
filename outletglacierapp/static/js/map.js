/* Display Greenland app */
/* requires: plotting.js */

var map = {};


/* Initialize the map (to be executed on document load */
map.init = function(callback) {

  console.log('map-init')

  // user interface (buttons and so on)
  map.ui = {};
  map.ui.$form = $("#map-config-form"); // form 
  map.ui.$submit = $("#map-refresh-toolkit"); // submit button
  map.ui.$refresh = $(".refresh"); // submit button
  map.ui.$reset = $("#map-reset-toolkit"); // submit button

  // initialize plot elements
  map.chart = map.makeMap()
    .xlabel('False Easting (km)')
    .ylabel('False Northing (km)')  // axes etc...

  // get glacier info for initialization
  $.getJSON('/glacierinfo', function(json) {

    map.glacierinfo = json.glacierinfo;

    // view / glacier coordinates (connect form and buttons)
    map.coordsCtrl = new coordsController();
    map.colorCtrl = new colorController();
    map.addWidgetBoxZoom();

    if (callback) {callback();};

  });

  map.ui.$submit.click(function(event) {
    console.log("submit")
    map.get_and_update_data();
    event.preventDefault();
  });

  map.ui.$reset.click(function(event) {
    // console.log("reset")
    // $.post('/reset', '', function(html) {} )
    // map.get_and_update_data();
    $.post('/reset', '', function() {
      window.open('/', '_self') // on callback open new link
    } )
    event.preventDefault();
  });
};

/*********************************************************
 * Fetch map data from the server
 *********************************************************/

map.get_and_update_data = function () {

  var configform = map.ui.$form.serializeArray(); // get all data from the $configform form and send to server

  map.ui.$submit.button('loading')

  console.log(configform)

  if (configform.length == 0) {
    console.error("empty form")
  }

  $.ajax({
    url: '/mapdata',
    data: configform,
    type: "GET",
    dataType : "json",
    success: function( json ) {
      console.log('data received OK');
      map.ui.$submit.button('reset');
      map.update_map(json);
    },
    error: function( xhr, status, errorThrown ) {
      var w = window.open(null, "_self")
      w.document.write(xhr.responseText)
      w.document.close()
      console.log( "Error: " + errorThrown );
      console.log( "Status: " + status );
      console.dir( xhr );
      // alert( "Error when receiving data from server." );
      map.ui.$submit.button('reset');
    }
  });

};

/*********************************************************
 * Callbacks when receiving new json data 
 *********************************************************/
map.update_map = function(json) {
  
  // replace missing values with NaN
  var ny = json.values.length;
  var nx = json.values[0].length;
  for (var i=0;i<ny;i++) {
    for (var j=0;j<nx;j++) {
      if (json.values[i][j] === json.missing) {
        json.values[i][j] = NaN;
      }
    }
  }

  map.chart
    .data(json) // update data
    .clabel(json.variable + ' ('+json.units+')')

  if (map.colorCtrl.isAuto()) {
    map.colorCtrl.setAuto();
  };
  map.chart
    .call()  // update plot
    .aspect(1);

  // also other dependencies
  for (var i=0; i<map.dependencies.length; i++) {
    map.dependencies[i].call(); // update: by convention, call to refresh
  }
};

map.dependencies = []; // update after map data is updated


/********************************************
 *  Controllers for the map UI 
 *  *****************************************/

/* help coordinate between coords, glacier and so on */
var coordsController = function(name, coords) {
    
    // define controllers from form
    var $left,$right,$top,$bottom,$glacier,$dataset,$maxpixels
      
    // coordinates
    $left = $("#left");
    $right = $("#right");
    $top = $("#top");
    $bottom = $("#bottom");

    // pre-defined coordinates
    $glacier = $("#glacier");
    $dataset = $("#dataset");
    $maxpixels = $("#maxpixels");

    this.name = name || $glacier.val(); // initialize from form 

    this.coords = coords || [$left.val(), $right.val(), $bottom.val(), $top.val()]; // left, right, bottom, top

    this.equalCoords = function(check) {
      return (this.coords[0] === check[0] 
        && this.coords[1] === check[1] 
        && this.coords[2] === check[2] 
        && this.coords[3] === check[3]);
    };

    this.setCoords = function(coords) {
      if (this.equalCoords(coords)) return; // do nothing if no change
      this.coords = coords;
      this.updateForm();
    };
     
    this.setGlacier = function(name) {
      var matches = map.glacierinfo.filter(function(d) {return d.name === name;});
      if (matches.length !== 1) {
        alert(name +" not found in database. Retry in a few moments?");
        return;
      };
      this.name = name;
      this.setCoords(matches[0].coords);
      return;
    };

    this.updateForm = function() {
      // update coords form
      $left.val(this.coords[0]);
      $right.val(this.coords[1]);
      $bottom.val(this.coords[2]);
      $top.val(this.coords[3]);
      $glacier.val(this.name)
      return;
    };

    // submit on dataset change
    $dataset.change(map.get_and_update_data)
    $maxpixels.change(map.get_and_update_data)
    // $maxpixels.keypress(function(event) { return event.keyCode != 13; });
    // Prevent enter (13) from submitting the form
    $maxpixels.keypress(function(event) { 
      if (event.keyCode == 13) {
        map.get_and_update_data(); 
        event.preventDefault(); // do not submit the form
      } else { 
        true;
      } 
    });

    // relate glacier button and coordinates
    ctrl = this; 

    $glacier.change(function(event) {
      // update coordinates accordingly
      ctrl.setGlacier($glacier.val());
      map.get_and_update_data();
    });

    var btn, btns = [$left, $right, $bottom, $top];
    for (var i=0; i<4; i++) {
      btn = btns[i];
      btn.change(function() {
        // update coordinates and update form
        ctrl.coords[i] = btn.val(); 
        ctrl.setCoords(ctrl.coords);
        ctrl.name = 'Custom';
      });
    };

    // attach events on zoom
    map.chart.on('zoom.update_coords', function (event) {

      // get the new domain
      var xrange = map.chart.x.domain();
      var yrange = map.chart.y.domain();

      // update map coordinates in the form
      map.coordsCtrl.setCoords([xrange[0], xrange[1], yrange[0], yrange[1]])
      map.coordsCtrl.name = "Custom" // set name to custom

      // fetch new data?
      // map.get_and_update_data();
    });
};

// Handle color controller
var colorController = function() {

  // Toggle between manual and automatic range
  var $crange_toggle = $("#color-range-btn");
  var $crange_field = $("#color-range");
  var $crange_min = $("#color-min");
  var $crange_max = $("#color-max");

  var m = map.chart;

  this.setAuto = function(){
      $crange_toggle.text("autoscale"); // mode to start with
      m.crange('auto'); 
      $crange_field.hide(); // hide min/max fields
  };

  this.setManual = function(){
      $crange_toggle.text("scale"); // mode to start with
      this.updateForm();
      $crange_field.show(); // hide min/max fields
  };

  $crange_toggle.text("autoscale"); // mode to start with

  this.isAuto = function() {
    return $crange_toggle.text() === "autoscale";
  };

  var ctrl = this;

  // update crange from figure
  this.updateForm = function() {
    var crange = m.crange(); // update field with actual values
    $crange_min.val(crange[0]);
    $crange_max.val(crange[1]);
  };

  // action 1: toogle between automatic and custom mode
  $crange_toggle.click( function() {
    if (ctrl.isAuto()) {
      // set manual 
      ctrl.setManual();
    } else {
      // set auto
      ctrl.setAuto();
    }
    ctrl.refresh()
  });


  ctrl.refresh = function() {
    if (ctrl.isAuto()) {
      m.crange('auto');
      m.call();
    } else {
      var crange = [parseFloat($crange_min.val()), parseFloat($crange_max.val())];
      if (isNumber(crange[0]) && isNumber(crange[1])) {
        m.crange(crange);
        m.call();
      } else {
        this.updateForm(); // reset fields
      };
    };
  };

  // action 2: modify custom values
  $crange_min.change(function () {
    ctrl.refresh();
  })
  $crange_max.change(function () {
    ctrl.refresh();
  })

  // (hidden refresh color button)
  // $("#color-refresh-btn").click(function () {
  // })
  $("#color-refresh-btn").hide(); // only triggered via Enter

  function isNumber(n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
  };

  $crange_toggle.prop("active", ! this.isAuto()); // make it inactive when auto

}


/****************************************
 Actual map, with canvas, zoom and so on
 ****************************************/

// HTML containers
map.map_container = '#map-figure'; 

// event: don't activate zoom-related functions if that key is not pressed
// plt.zoom_press_key = 'ctrlKey';
map.zoom_press_key = undefined;

/************
 *
 * This section make the map and deals with simple events
 *
 * ***********/
  
map.makeMap = function() {

  console.log('makeMap')
  /* USAGE:
   *
   * mymap = plt.makeMap(); // set up the canvas and svg elements
   *
   * mymap.data(newdata)(); // bind data and refresh
   * mymap.crange(color_range)(); // update color range and refresh
   *
   * mymap
   *  .data(newdata)
   *  .crange(color_range) (); // all combined
   */

  var jsondata ; // global data

  // var palette = ["#eff3ff", "#6baed6", "#08519c"]; 
  var palette = ['rgb(215,48,39)','rgb(244,109,67)','rgb(253,174,97)','rgb(254,224,144)','rgb(255,255,191)','rgb(224,243,248)','rgb(171,217,233)','rgb(116,173,209)','rgb(69,117,180)'].reverse();

  var missing_data_color = "white";

  var total_width = 750,
      total_height = 500;

  var margin = { top: 20, 
                 left: 50, 
                 bottom: total_height*.9, 
                 right: total_width *.85};

  var width = margin.right-margin.left,
      height = margin.bottom - margin.top;

  var colorbar_margin = { top: margin.top, 
                          left: margin.right + 0.03*width, 
                          bottom: margin.bottom, 
                          right: total_width-30};

  // colorbar anchor point and size (relatively to canvas origin, top left)
  var colorbar_width = width*0.03;
  var colorbar_length = (margin.bottom-margin.top-1)*1;
  var colorbar_anchor_x = colorbar_margin.left - margin.left; 
  var colorbar_anchor_y = (margin.bottom-margin.top+1-colorbar_length)/2;

  // axis labels positioning
  var xlabel_offset = 40; // vertical offset
  var ylabel_offset = -40; // horizontal offset
  var clabel_offset = 50;  // horizontal offset for the colorbar

  // data dimensions (ny, nx)
  var nx, ny;

  var ctx;
  var imageObj = new Image();

  var x = d3.scale.linear()
          .range([0, width]);

  var y = d3.scale.linear()
          .range([height, 0]);

  var xAxis = d3.svg.axis()
          .scale(x)
          .orient("bottom")

  var yAxis = d3.svg.axis()
          .scale(y)
          .orient("left")

  var zoom = d3.behavior.zoom()
          .x(x)
          .y(y)
          // .scaleExtent([1, 10])
          .on("zoom", onzoom)
          .on("zoomend", function() {
            // only refresh on panning and zoom out
            if (zoom.scale() === 1) map.get_and_update_data()
            });

  // http://bl.ocks.org/garrilla/11280861
  // var panExtent = {x: [-180, 180], y: [-90, 90] };
  var panExtent = {x: [-Infinity, Infinity], y: [-Infinity, Infinity] };

  var color = d3.scale.linear()
      .domain(map.linspace(0, 1, palette.length)) // default to 0, 1
      .range(palette);

  var $container = d3.select(map.map_container);

  var canvas = $container.append("canvas")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
          .attr("x", margin.left).attr("y", margin.top )
          .attr("class", "map")
          .style("left", margin.left + "px")
          .style("top", margin.top + "px")
          .style("width", width + "px")
          .style("height", height + "px")

  var svg = $container.append("svg")
      .attr("width", total_width)
      .attr("height", total_height)
    .append("g")
      .attr("id","canvas-origin")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  console.log('append cannvas-origin')
  console.log(svg)

  // make a mask for clipping
  var defs = svg.append('defs')
      .append('clipPath')
      .attr('id', 'canvas-clip')
      .append("rect")
      .attr("width", width)
      .attr("height", height)

  // add groups for axes
  svg.append("g")
          .attr("class", "y axis map")
          .call(yAxis)

  svg.append("g")
          .attr("class", "x axis map")
          .attr("transform", "translate(0, "+ height + ")")
          .call(xAxis)

  var colorbar = Colorbar()
    .origin([0,0]) // relatively to colorbar context
    .scale(color)
    .barlength(colorbar_length) // bug without -1
    .thickness(colorbar_width); 

  var colorbar_context = svg.append("g")
          .attr("class", "colorbar")
          .attr("transform", "translate(" + colorbar_anchor_x + ","+colorbar_anchor_y+")");
          //.call(colorbar)
            
  // axis labels
  var xlabel = svg
          .append("text")
          .attr('class','map x axis label')
          .attr('x', width/2)
          .attr('y', height+xlabel_offset)
          .attr("text-anchor", "middle")
          //.text("");

  var ylabel = svg
          .append("text")
          .attr('class','map y axis label')
          .attr('x', ylabel_offset) // -30 also below
          .attr('y', height/2) 
          .attr('transform','rotate(-90, '+ylabel_offset+','+height/2+')')
          .attr('text-anchor','middle')
          //.attr('transform','rotate(-90,0,'+height/2+')translate(-30,-30)')
          //.text("Latitude (\u00B0N)");

  var clabel = colorbar_context
          .append("text")
          .attr('class','map colorbar axis label')
          .attr('x', colorbar_width+clabel_offset) 
          .attr('y', height/2) 
          .attr('transform','rotate(-90, '+(colorbar_width+clabel_offset)+','+height/2+')')
          .attr('text-anchor','middle')
          //.attr('transform','rotate(-90,0,'+height/2+')translate(-30,-30)')
          //.text("Sea level rise since "+plt.$baseyear.val()+" (m)");

  var heatmap;

  // add rectangle of same size as the canvas to capture mouse events 
  // (as it is useful to interact with other svg elements on top of the canvas)
  // the canvas is more convenient as background
  var event_listener = svg.append("rect")
      .attr("id", "canvas-overlay")
      .attr("width", width)
      .attr("height", height)
      .style("opacity", 1e-6) // invisible
      .style("fill", "000")
      .call(zoom)
      .on("dblclick.zoom", null);

  function myMap() {
      nx = heatmap[0].length,
      ny = heatmap.length;
      d3.select("canvas")
          .attr("width", nx)
          .attr("height", ny)
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
          .call(drawImage);

      // update colorbar
      colorbar_context.call(colorbar);

      refresh();

      return myMap;
  };

  // Compute the pixel colors; scaled by CSS.
  var img;
  function drawImage(canvas) {
      ctx = canvas.node().getContext("2d");
      //var nx = heatmap.length
      //var ny = 180;
      var v, c; 
      var img = ctx.createImageData(nx, ny);
      for (var y = ny-1, p = -1; y >= 0; --y) {
          for (var x = 0; x < nx; ++x) {
              v = heatmap[y][x];
              if (map.isNumber(v)) {
                c = d3.rgb(color(v));
              } else { 
                c = d3.rgb(missing_data_color);
              }
              img.data[++p] = c.r;
              img.data[++p] = c.g;
              img.data[++p] = c.b;
              img.data[++p] = 255;
          }
      }
      // Keeping pixels as nearest neighbor (as anti-aliased as we can get
      // without doing more programming) allows us to see how the marginals
      // line up when zooming in a lot.
      ctx.mozImageSmoothingEnabled = false;
      ctx.webkitImageSmoothingEnabled = false;
      ctx.msImageSmoothingEnabled = false;
      ctx.imageSmoothingEnabled = false;
      ctx.putImageData(img, 0, 0);
      imageObj.src = canvas.node().toDataURL();
  }

  /* EVENTS */

  // The code below enforces that a special key is pressed to allow 
  // zooming, but panning remains allow under all circunstances.
  var lastZoomState;
  updateZoom();

  function cancelZoom() {
    zoom.translate(lastZoomState.translate);
    zoom.scale(lastZoomState.scale);
  };
  function updateZoom() {
    lastZoomState = {'scale':zoom.scale(), 'translate':zoom.translate()};
  };
  
  // triggered first on zoom event
  function onzoom() {
      if (map.zoom_press_key 
            && !d3.event.sourceEvent[map.zoom_press_key] 
            ) {
        cancelZoom();
        return;
      } 
      // update
      updateZoom();
      /* call the zoom.translate vector with the array returned from panLimit() */
      zoom.translate(panLimit());
      refresh();
  }

  function panLimit() {
  /*
  http://bl.ocks.org/garrilla/11280861
  include boolean to work out the panExtent and return to zoom.translate()
  */

  var divisor = {h: height / ((y.domain()[1]-y.domain()[0])*zoom.scale()), w: width / ((x.domain()[1]-x.domain()[0])*zoom.scale())},
    minX = -(((x.domain()[0]-x.domain()[1])*zoom.scale())+(panExtent.x[1]-(panExtent.x[1]-(width/divisor.w)))),
    minY = -(((y.domain()[0]-y.domain()[1])*zoom.scale())+(panExtent.y[1]-(panExtent.y[1]-(height*(zoom.scale())/divisor.h))))*divisor.h,
    maxX = -(((x.domain()[0]-x.domain()[1]))+(panExtent.x[1]-panExtent.x[0]))*divisor.w*zoom.scale(),
    maxY = (((y.domain()[0]-y.domain()[1])*zoom.scale())+(panExtent.y[1]-panExtent.y[0]))*divisor.h*zoom.scale(), 

    tx = x.domain()[0] < panExtent.x[0] ? 
        minX : 
        x.domain()[1] > panExtent.x[1] ? 
          maxX : 
          zoom.translate()[0],
    ty = y.domain()[0]  < panExtent.y[0]? 
        minY : 
        y.domain()[1] > panExtent.y[1] ? 
          maxY : 
          zoom.translate()[1];
  
    return [tx,ty];

  }

  // Refresh image after a zoom event
  function refresh() {

      var t = zoom.translate();
      var s = zoom.scale();
      var tx = t[0],
          ty = t[1];

      // save and restore because clearRect can reset zoom state
      // but apparently not ==> commented out for now
      // ctx.save();
      ctx.clearRect(0, 0, imageObj.width, imageObj.height);
      // ctx.restore();
      //

      ctx.drawImage(imageObj, 
          tx*imageObj.width/width, ty*imageObj.height/height,
          imageObj.width*s, imageObj.height*s);

      svg.selectAll(".x.axis.map").call(xAxis);
      svg.selectAll(".y.axis.map").call(yAxis);

      // // another clip for non-skewed points on the canvas
      // svg.select("defs #canvas-clip").select('rect')
      //   .attr("transform", "scale(" + 1/s + ")")
      //   .attr("x",0-t[0]) // origin is 0,0
      //   .attr("y",0-t[1])
  }

  // return mouse position with appropriate truncation
  myMap.get_mouse_info = function(event) {

    var coords = d3.mouse(event);

    // real coordinates
    var xx = x.invert(coords[0]),
        yy = y.invert(coords[1]);

    // format to 1 digit precision
    var value = myMap.get_value(xx, yy);

    xx = d3.round(xx,1);
    yy = d3.round(yy,1);

    // plt.writeInfoBox({x:xx, y:yy, value:value, units:jsondata.units});
    return {x:xx,y:yy,value:value,units:jsondata.units};
  };

  myMap.get_value = function(xx, yy) {

    // axis value to indices
    var convert = {};
    convert.ix = d3.scale.linear().domain(jsondata.x_range).rangeRound([0,nx-1])
    convert.iy = d3.scale.linear().domain(jsondata.y_range).rangeRound([0,ny-1])

    var ix = convert.ix(xx)
    var iy = convert.iy(yy)

    var value = heatmap[Math.floor(iy)]; // can be undefined
    if (value) {value = value[Math.floor(ix)]};

    return value;
  };

  // add box to display coordinates
  var infobox = map.addInfoBox({'event_listener':event_listener, 'svg':svg, 'get_mouse_info':myMap.get_mouse_info});

  function autorange() {
    // automatically update data based on color range
      
    // // Min / max range from data  
    // // determine data range 
    var flatdata = map.flatten(heatmap); // flatten values
    var crange = d3.extent(flatdata); // check extent
      
    // Use 5/95 percentiles provided as argument
    // var crange = [jsondata.minc, jsondata.maxc];
    // var crange = jsondata.data_range;
    var domain = map.linspace(crange[0], crange[1], palette.length);
      
    // update color domain
    color.domain(domain);

    // round the range
    color.nice();

    // new update with nice range
    var domain = color.domain();
    domain = map.linspace(domain[0], domain[domain.length-1], palette.length);
    color.domain(domain);

  }

  // resize figure
  function set_aspect(r) {

    // new width
    var dh = y(0) - y(1);
    var dw = x(1) - x(0);
    var aspect = dw / dh; // old aspect ratio
    var w = width * r / aspect; // new width to match new aspect ratio
    
    // change from previous
    tx = w - width;

    width = w;
    total_width += tx;

    // margin
    margin.right = margin.left + width; 

    // update svg
    var svg = $container.select('svg');
    svg.attr("width", total_width);

    // update canvas
    canvas.style("width", width + "px")

    // update scales and their dependencies
    x.range([0, width]);

    // axes
    xAxis.scale(x);

    // zoom behavior
    zoom.x(x);

    // label
    xlabel.attr('x', width/2)

    colorbar_anchor_x += tx;

    // update the colorbar position
    colorbar_context
          .attr("transform", "translate(" + colorbar_anchor_x + ","+colorbar_anchor_y+")");

    // overlay
    event_listener.attr('width', width)

    // update clip path
    defs.attr('width',width);

    // svg.call(xAxis)
    refresh();
  };


  /*************************************************
   * Getter / setter methods accessible from the outside
   *************************************************/

  myMap.data = function(json) {
    if (!arguments.length) {return jsondata};

    jsondata = json;

    heatmap = json.values;
    ny = heatmap.length;
    nx = heatmap[0].length;

    //also update axis range
    x.domain(json.x_range);
    y.domain(json.y_range);

    zoom.x(x);
    zoom.y(y);

    return myMap;
  }

  myMap.crange = function(values) {
    // set color range
    // this is made complicated by the fact that the palette
    // used can be (and is) longer than 2 elements.
    // more over, certain values may be nan or string

    // getter
    if (!arguments.length) {
      var cdom = color.domain();
      var crange = [cdom[0], cdom[cdom.length-1]];
      return crange;
    };

    // setter
    var crange = values; // update

    // define / update colorscale
    if (crange === 'auto') {
      autorange();
    } else {
      color.domain(map.linspace(crange[0], crange[1], palette.length)) // default to 0, 1
    };
      
    return myMap;
  }

  myMap.xlabel = function(label) {
    if (!arguments.length) {return xlabel.text();}
    xlabel.text(label);
    return myMap;
  }

  myMap.ylabel = function(label) {
    if (!arguments.length) {return ylabel.text();}
    ylabel.text(label);
    return myMap;
  }

  myMap.clabel = function(label) {
    if (!arguments.length) {return clabel.text();}
    clabel.text(label);
    return myMap;
  }

  // register new event listeners
  myMap.on = function(eventType, callback) {

    // http://stackoverflow.com/questions/646628/how-to-check-if-a-string-startswith-another-string)
    function startswith(str1, str2) {
      return str1.lastIndexOf(str2, 0) === 0;
    };

    // for behaviours, update behaviour instead of event Listeners
    if (startswith(eventType,'zoom')) {
      return zoom.on(eventType, callback);
    }
    if (startswith(eventType,'drag')) {
      return drag.on(eventType, callback);
    }

    // standard events, just attach them to event_listener g
    return event_listener.on(eventType, callback);
  }

  // Set plot limit, for example aspect ratio
  myMap.aspect = function(value) {
    if (!arguments.length) {return (x(1)-x(0)) / (y(0) - y(1)) ;}
    set_aspect(value);

    return myMap;
  };

  ///// To be cleaned up at some point 

  myMap.canvas = canvas;
  myMap.svg = svg; // svg element representing the inside surface

  myMap.infobox = function() {
    return infobox;
  }

  // myMap.zoom = function() { return zoom; };
  myMap.zoom = zoom;

  // make the map accessible at the module level
  map.chart = myMap;

  myMap.x = x;
  myMap.y = y;
  myMap.color = color;

  // attach heatmap for checking
  myMap.heatmap = function() {
    return heatmap;
  }
  myMap.refresh = refresh;
  return myMap;
}

/*******************************************
 * Info box containing coordinate and value 
 * info 
 *******************************************/
map.addInfoBox = function(o) {

  // info box to display coordinates
  var infobox_anchor_x = 0;
  var infobox_anchor_y = -5;

  var svg = o.svg;
  var event_listener = o.event_listener;
  var get_mouse_info = o.get_mouse_info;

  // text element to indicate the figure coordinates
  var infobox = svg
          .append("text")
          .attr('class','map infobox')
          .attr('transform','translate('+infobox_anchor_x+', '+infobox_anchor_y+')') // small offset
          .style("width", 40)
          .style("height",20)
          .style('position', 'relative');

  var info, message;

  event_listener
    .on('mousemove', function() {
      // get data as object
      info=get_mouse_info(this);
      // Formatted message
      message=info.x+", "+info.y
      if (info.value && !isNaN(info.value)) {
        message+= " : "+info.value+" "+info.units;
      }
      infobox.text(message);
    })
    .on('mouseout', function() {
      infobox.text("");
    })

  return infobox;

};

/**************************** 
 *
 * Utility functions, mostly for the map
 *
 *****************************/

map.inflate = function(values1D, nx, ny) {
  // inflate 1-D data to 2d
  // shape (ny, nx) indexed by (i, j)
  var values2D = [];

  var kk = 0;
  for ( var i=0; i<ny; i++) {
    newline = [];
    for (var j=0; j<nx; j++) {
      kk++   // increment the counter
      newline.push(values1D[kk])
    }
    values2D.push(newline);
  }
  return values2D
}

map.flatten = function(values2D) {
  // flatten 2-D data (list of list) to 1-D
  // list of horizontal rows
  var ny = values2D.length;
  var nx = values2D[0].length;
  var values1D = [];
  for (var i=0; i<ny; i++) {
    for (var j=0; j<nx; j++) {
    values1D.push(values2D[i][j]);
    }
  }
  return values1D;
}

map.linspace = function(cmin, cmax, n) {
    // build up domain that match the palette
    var domain = [];
    for (var i=0; i<n; i++) {
      domain[i] = cmin + (cmax-cmin)*i/(n-1);
    }
    return domain;
}

map.isNumber = function(n) {
  return !isNaN(parseFloat(n)) && isFinite(n);
};

// make a brush for box zoom
map.addWidgetBoxZoom = function() {

  var $boxzoom=$('<input id="widget-boxzoom" type="button" value="BoxZoom"/>')
  // var $boxzoom=$('<input id="widget-boxzoom" type="button" img="/static/images/boxzoom-icon.png" />')
  // var $boxzoom=$('<icon id="widget-boxzoom" img="/static/images/boxzoom-icon.png"></icon>')
    .attr("class","btn btn-primary")
    //.appendTo("#map-toolkit")
    .insertBefore("#map-refresh-toolkit")
    .on("click", function() {
      // toggle brush listener

      var brushelements = d3.selectAll('#map-figure rect.extent')
      console.log(brushelements)
      if (!brushelements[0].length) {
        setbrush();
      } else {
        clearbrush();
      }
      // var pt_evt = brushListener.style('pointer-events');
      // pt_evt = pt_evt === 'all' ? 'none' : 'all' ; // toggle
      // if (pt_evt==='none') {
      //   clearbrush();
      // } else {
      //   setbrush();
      // }
    })

  // work arounds to get brushstart, move and end to work
  function setbrush() {
    brush.clear();
    console.log("set brush")
    brushListener.call(brush).call(brush.event);
    brushListener.on('mousedown.bush', brushstart)
    d3.select('#canvas-overlay')
    .on('mousemove.brush', brushmove)
    .on('mouseup.brush', brushend)
    brushListener.style('pointer-events', 'all');
  }

  function clearbrush() {
    console.log('clear brush')
    brushListener.call(brush.clear());
    brushListener.on('mousedown.brush', null)
    d3.select('#canvas-overlay')
      .on('mousemove.brush', null)
      .on('mouseup.brush', null)
    brushListener.style('pointer-events', 'none');
    brush.clear()
    brush.empty()
    d3.selectAll('#map-figure .brush rect,#map-figure .brush g').remove()
  }

  var brush = d3.svg.brush()
    .x(map.chart.x)
    .y(map.chart.y)
    // .on('brushstart', brushstart)
    // .on('brush', brushmove)
    // .on('brushend', brushend)

  // add a brushable element
  var brushListener = d3.select('#canvas-origin')
    .append('g')
    .attr('class','brush')
    .style('pointer-events', 'none');

  // var svg = svg_ || d3.select('svg');
  // use simple closure for brush
    
  // on brush
  var brushCell = null;
    
  // Clear the previously-active brush, if any.
  var brushstart = function(p) {
    console.log('brushstart')
    // if (brushCell !== this) {
    //   // d3.select(brushCell).call(brush.clear());
    //   d3.select(brushCell).call(brush.clear());
    //   brushCell = this;
    // }
  }

  var brushmove = function() {
    console.log('brushmove')
    var e = brush.extent();
    map.name = "Custom";
    map.coordsCtrl.setCoords([e[0][0], e[1][0], e[0][1], e[1][1]])
  }

  // If the brush is empty, select all circles.
  var brushend = function() {
    console.log('brushend')
    var e = brush.extent();
    map.name = "Custom";
    map.coordsCtrl.setCoords([e[0][0], e[1][0], e[0][1], e[1][1]])
    // brushListener.call(brush.clear());
    //  turn off
    // $boxzoom.trigger();
    map.get_and_update_data();

    clearbrush();
  }

  return brush;
}


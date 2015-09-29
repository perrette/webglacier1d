/* load google map */

var map, lines;

function initialize() {
  // Create a simple map.
  map = new google.maps.Map(document.getElementById('map-canvas'), {
    zoom: 3,
    center: {lat: 76, lng: -40},
    mapTypeId: google.maps.MapTypeId.TERRAIN
  });

  // Load a GeoJSON from the same server as our demo.
  map.data.loadGeoJson('https://storage.googleapis.com/maps-devrel/google.json');

  // // Add drawing tool
  // var drawingManager = new google.maps.drawing.DrawingManager({
  //   // drawingMode: google.maps.drawing.OverlayType.POLYLINE,
  //   drawingControl: true,
  //   drawingControlOptions: {
  //     position: google.maps.ControlPosition.TOP_CENTER,
  //     drawingModes: [
  //       google.maps.drawing.OverlayType.POLYLINE,
  //     ]
  //   }
  // });
  // drawingManager.setMap(map);

  // get line data 
  lines = [];
  $.getJSON('/lineslonglat', function(json) {
    json.longlatlines.forEach(function(line) {
      var gpoints = line.values.map(function(pt) {
        return new google.maps.LatLng(pt.y, pt.x);
      });

      var gline = new google.maps.Polyline({
        path: gpoints,
        strokeColor: '#FF0000',
        strokeOpacity: 1.0,
        strokeWeight: 2,
        editable: true
      });

      function on_path_changed(event) {
        var path = gline.getPath();
        // Get new long lat
        // console.log(path)
        console.log("path changed !")
      }

      gline.setMap(map)

      // Add an event listener on the line.
      // google.maps.event.addListener(gline, 'bounds_changed', on_path_changed);
      google.maps.event.addListener(gline, 'mouseup', on_path_changed);

      lines.push({id:line.id, gline:gline}); // keep track
    })
  })
}

$(document).ready( function() {
  drawing.addToolkit();
})


// Contains functions useful to interact with Google Map API
var gmaptools = {};

// function to extract x, y coordinates of points along a polyline.
gmaptools.get_polyline = function(gline) {
  var at;  // point coordinates
  var path = gline.getPath(); // path of a polyline
  var res = []; // result to be filled
  for (var i=0; i<path.getLength(); i++) {
    at = path.getAt(i);
    res.push( {x: at.L, y: at.H} );
  };
  return res;
} ;


// override drawing functions to work with googlemap
drawing.getLines = function() {
  return lines.map(function(d){
    return {
      id: d.id,
      values: gmaptools.get_polyline(gline)
    }
  })
}

drawing.updateID = function(oldid, newid) {
  lines
    .filter(function(line) {return line.id === oldid;})
    .forEach(function(line) {line.id = newid;})
}

drawing.linesURL = '/lineslonglat';

google.maps.event.addDomListener(window, 'load', initialize);

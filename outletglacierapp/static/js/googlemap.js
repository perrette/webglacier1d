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

  // modify a few things
    
  // $("#save-lines")
  // .on('click', function() {
  //   postLinesToServer( function() {console.log('lines saved')});
  // })
  //
  // $("#download")
  // .on('click', function() {
  //   postLinesToServer( function() {
  //     
  //   });
  // })
})

// override drawing functions to work with googlemap
drawing.getLines = function() {
  // get line coordinates
  return lines.map(function(d){
    return {
      id: d.id,
      values: d.gline.getPath().j.map(function(df) {
        return {
          x:df.B,
          y:df.k
        }
      })
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

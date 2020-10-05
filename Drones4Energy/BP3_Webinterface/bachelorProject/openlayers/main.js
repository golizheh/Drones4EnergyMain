import 'ol/ol.css';
import GeoJSON from 'ol/format/GeoJSON';
import Map from 'ol/Map';
import Overlay from 'ol/Overlay';
import VectorImageLayer from 'ol/layer/VectorImage';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import {Fill, Stroke, Circle, Style, Text, Icon} from 'ol/style';
import GeometryType from 'ol/geom/GeometryType';
import TileJSON from 'ol/source/TileJSON';
import {MultiPoint, Point, LineString} from 'ol/geom';
import Feature from 'ol/Feature';
import {fromLonLat, transform} from 'ol/proj';
import {getVectorContext} from 'ol/render';
// jquery import
import {$,jQuery} from 'jquery';

// variables needed for the popup
// ved ikke hvorfor den her er der? var element = document.getElementById('popup1');
var container = document.getElementById('popup');
var content = document.getElementById('popup-content');
var closer = document.getElementById('popup-closer');

// #################### The Styles ##################

// style for the error icon
var errorStyle = new Style({
  image: new Icon({
    scale: 0.06,
    src: 'data/marker.png'
  })
});

// drone style
var droneStyle = new Style({
  image: new Circle({
    radius: 5,
    fill: new Fill({color: 'yellow'}),
    stroke: new Stroke({color: 'red', width: 1})
  })
});

// style for the selected towers
var highlightStyle =
   new Style({
     image: new Circle({
       radius: 7,
       fill: new Fill({
         color: 'rgba(51, 255, 153, 1)'
       }),
       stroke: new Stroke({
         color: 'rgba(70, 70, 70, 1)',
         width: 2
       })
     })
  });

  var tower_style =
     new Style({
       image: new Circle({
         radius: 5,
         fill: new Fill({
           color: 'rgba(255, 255, 255, 0.8)'
         }),
         stroke: new Stroke({
           color: 'rgba(85, 85, 85, 1)',
           width: 1
         })
       })
    });

  var no_zone_style =
    new Style({
      stroke: new Stroke({
        color: 'rgba(255, 0, 0, 0.4)',
        width: 1
      }),
      fill: new Fill({
        color: 'rgba(255, 0, 0, 0.1)'
      })
  });

// #################### END OF the styles ##################

// #################### Layers on the map and the map itself ##################

// map layer
var mapLayer = new TileLayer({
     source: new OSM()
  })

  //The mappping for zones
  var vectorLayer_noZone = new VectorImageLayer({
    source: new VectorSource({
      format: new GeoJSON(),
  	 url: 'no_zone.geojson'
    }),
    style: no_zone_style
  });

//the mapping of the electirc towers
var vl_tower = new VectorImageLayer({
  source: new VectorSource({
    format: new GeoJSON(),
	 url: 'export1.geojson'
  }),
  style: tower_style
});

// overlay for the popup
var overlay_popup = new Overlay({
 element: container,
 autoPan: true,
 autoPanAnimation: {
   duration: 250
 }
});

//Route layer
var vectorLayer_route = new VectorLayer({
  source: new VectorSource({
  })
});

// vector layer for the error icon
var vectorLayer_error = new VectorLayer({
  source: new VectorSource({
  }),
  style: errorStyle
});

//drone layer
var vl_drones = new VectorLayer({
  source: new VectorSource({
  })
});

// #################### END OF Layers on the map and the map itself ##################

// #################### The map setup ##################
//the view for the map, set fiex on denmark
var view = new View({
  center: [1130000,7590000],
  zoom: 7.7
});

// init the map with all the layers and overlay for popup
var map = new Map({
  target: 'map-container',
  layers: [mapLayer, vl_tower, vectorLayer_error, vl_drones, vectorLayer_route, vectorLayer_noZone],
  overlays: [overlay_popup],
  view: view
});

// #################### END OF The map setup ##################

// #################### Drones ##################
var drone1 = new Feature({
   geometry: new Point(fromLonLat([10,56])),
   name: 'drone',
   id: 1,
   // work types: n=none, r=recharge, w=working
   work: 'n'
});

drone1.setStyle(droneStyle);
vl_drones.getSource().addFeature(drone1);

var drone_dict = {};
drone_dict[1] = drone1;

// #################### END OF Drones ##################

// #################### The clicker function ##################

// array for the selected towers
var selected = [];
// dictionary for errors with coordinates as keys and images as values
var error_dict = {};
//var for which error site we are looking at
var error_selected;

// click on function on the different layers on the map
map.on('singleclick', function(e) {
   // event e call on a feature f
   map.forEachFeatureAtPixel(e.pixel, function(f) {
      // if clicked on a error icon
      if ((f.get('name')) == "Error") {
         error_selected = f;
         document.getElementById("errorbar").style.width = "0";
         clean_images();
         // get the sidebar and images again for the new site
         document.getElementById("errorbar").style.width = "250px";
         get_images(transform(f.getGeometry().getCoordinates(), 'EPSG:3857', 'EPSG:4326'));
      // if clicked on a tower
   } else if ((f.get('power')) != undefined) {
         // insert tower into the selceted array
         var selIndex = selected.indexOf(f);
            if (selIndex < 0) {
               selected.push(f);
               f.setStyle(highlightStyle);
            // if diselected remove from list and remove style highlight
            } else {
               selected.splice(selIndex, 1);
               f.setStyle(undefined);{}
               //hvis der ikke er flere tilbage
               if (selected.length == 0) {
                  overlay_popup.setPosition(undefined);
                  closer.blur();
               }
            }
            //Så popup kun dukker op 1 gang
            if (selected.length == 1) {
               var coordinate = e.coordinate;
               //en knap til route. og en knap til slet alle punkter.
               content.innerHTML = '<p>Calculate route:</p>';
               overlay_popup.setPosition(coordinate);
            }
         }
   });
});

// #################### END OF The clicker function ##################

// #################### Drone icon render ##################

//render drones on map
var n = 1;
var omegaTheta = 60000; // Rotation period in ms
var R = 7e6;
var r = 2e6;
var p = 2e6;

mapLayer.on('postrender', function(e2){

   var vectorContext = getVectorContext(e2);
   var frameState = e2.frameState;
   var theta = 2 * Math.PI * frameState.time / omegaTheta;
   var i = 0;

   var t = theta + 2 * Math.PI * i / n;
   var x = (R + r) * Math.cos(t) + p * Math.cos((R + r) * t / r);
   var y = (R + r) * Math.sin(t) + p * Math.sin((R + r) * t / r);

   vectorContext.setStyle(droneStyle);
   vectorContext.drawGeometry(new Point([x, y]));

   map.render();
});
map.render();

// #################### END OF Drone icon render ##################

// #################### The popup ##################
var t_show_start = document.getElementById('btn_start');
var t_show_end = document.getElementById('btn_end');
var t_show_route = document.getElementById('btn_route');

// closer function for the popup
closer.onclick = function() {
   // empty the selected list
   while (selected.length > 0) {
      selected[selected.length-1].setStyle(undefined);
      selected.pop();
   }
   // remove rendered route
   vectorLayer_route.getSource().clear();

   // remove popop
   overlay_popup.setPosition(undefined);
   closer.blur();
   return false;
};

t_show_start.onclick = function() {
   //get the first selected tower
   var feature = selected[0];
   var point = feature.getGeometry();
   //fit the view for the point
   view.fit(point, {minResolution: 20})
}

t_show_end.onclick = function() {
   //get the first selected tower
   var feature = selected[selected.length-1];
   var point = feature.getGeometry();
   //fit the view for the point
   view.fit(point, {minResolution: 20})
};

// calculate route and show on map function
t_show_route.onclick = function() {
   //call astar and send the selected points here
   var data = [
      [10.4952056, 55.2358393],
      [10.4968662, 55.2344039],
      [10.4990299, 55.2325096],
      [10.5008294, 55.2309678],
      [10.5027461, 55.2293146],
      [10.5058977, 55.2287173],
      [10.5095206, 55.2280032],
      [10.5131102, 55.2273027],
      [10.5165236, 55.2266429],
      [10.5199704, 55.2259804],
      [10.5233682, 55.2260851],
      [10.5252622, 55.2261514],
      [10.525292642030786, 55.22615232937427],
      [10.5254572, 55.2247513],
      [10.5257751, 55.2217917],
      [10.5261808, 55.2184334],
      [10.5265371, 55.2155166],
      [10.5268933, 55.2123468],
      [10.5273006, 55.2090668],
      [10.5276665, 55.2062709],
      [10.5280046, 55.2032822],
      [10.5284553, 55.1998811],
      [10.5288162, 55.196857],
      [10.5292162, 55.1935297],
      [10.529584, 55.1903911],
      [10.530774, 55.1866252],
      [10.5319877, 55.1852603]
   ];
   // remove the code apove when done with call astar code

   // making al the lines for the route
   var feature_list =[];
   for (var i=0; i<=data.length-2; i++) {
      feature_list.push(new Feature({geometry: new LineString([fromLonLat(data[i]), fromLonLat(data[i+1])])}));

      var x = Math.trunc((255/(data.length-1))*i);
      var y = 255-x;

      feature_list[i].setStyle(
         new Style({
            stroke: new Stroke({
               color: 'rgba(0, '+x+', '+y+', 0.5)',
               width: 6,
            })
         })
      );
   };

   vectorLayer_route.getSource().addFeatures(feature_list);
   map.render;
};

// #################### END OF The popup ##################

// #################### error icons ##################

// get data from ros and make error icon every time drones return a error
var cords = [12.0453776, 55.4786747];
var img_list = ['data/Error.png', 'data/Error.png', 'data/Error.png'];

var cords2 =[10.529584, 55.1903911];
var img_list2 = ['data/Error.png', 'data/Error.png'];

// add the error to the dict for look up
error_dict[cords] = img_list;
error_dict[cords2] = img_list2;

//add the feature to the vectoru layer
vectorLayer_error.getSource().addFeatures([
   new Feature({
      geometry: new Point(fromLonLat(cords)),
      name: 'Error',
      id: 1
   })
]);

vectorLayer_error.getSource().addFeatures([
   new Feature({
      geometry: new Point(fromLonLat(cords2)),
      name: 'Error',
      id: 2
   })
]);


// #################### END OF error icon ##################

// #################### Error sidebar functions ##################

var error_close = document.getElementById('error_close_bnt');
var error_imgs = document.getElementById('error_imgs');
var reomve_error = document.getElementById('btn_remove_error');

// remove function for the error bar
reomve_error.onclick = function() {
   //clean the sidebar
   document.getElementById("errorbar").style.width = "0";
   clean_images();
   //remove the error site from the dict and the map
   delete error_dict[transform(error_selected.getGeometry().getCoordinates(), 'EPSG:3857', 'EPSG:4326')];
   vectorLayer_error.getSource().removeFeature(error_selected);
};

// close function for the error bar
error_close.onclick = function() {
   document.getElementById("errorbar").style.width = "0";
   clean_images();
};

// cleaning all the images in the sidebar
function clean_images () {
   while (error_imgs.hasChildNodes()) {
      error_imgs.removeChild(error_imgs.firstChild);
   }
};

// setting up the images from the error site, given the cordinates of the error site
function get_images (dict_lookup) {
   var img_data = error_dict[dict_lookup];
   for (var i=0; i <=img_data.length-1; i++) {
      // set atributes like source and width
      var error_img = document.createElement('img');
      error_img.src = img_data[i];
      error_img.style.width = "200px";
      //insert image
      document.getElementById('error_imgs').appendChild(error_img);
   }
};

// #################### END OF Error sidebar functions for close and images ##################


// ####################  Connecting to ROS  ####################
// -----------------
var ros = new ROSLIB.Ros({
   url : 'ws://localhost:9090'
});


// If there is an error on the backend, an 'error' emit will be emitted.
ros.on('error', function(error) {

  console.log(error);
});

// Find out exactly when we made a connection.
ros.on('connection', function() {
  console.log('Connection made!');

});

ros.on('close', function() {
  console.log('Connection closed.');
});
// #################### End of connecting to ROS ####################



// #################### All the ROS lisnters ####################
var drones = new ROSLIB.Topic({
   ros : ros,
   name : '/drones',
   messageType : 'beginner_tutorials/IntList'
});

drones.subscribe(function(message) {
  console.log('Received message on ' + drones.name + ': ' + message.data[0]);

  drone_dict[message.data[1]].getGeometry().setCoordinates(fromLonLat(data[0]));
  //tænker der kommer 2 messages ind, den gamle location og den nye, når en drone opdatere.
  // code der mangler: SLET GAMEL PRIK, SÆT EN NY PRIK.

});

/*var erros = new ROSLIB.Topic({
   ros : ros,
   name : '/erros',
   messageType : 'std_msgs/String'
});

errors.subscribe(function(message) {
  console.log('Received message on ' + errors.name + ': ' + message.data);
  //hvergang et billede bliver opdateret, så skal vi finde en måde at vide hvor det kom fra,
  // og så vise hvor det skal vises.
});

// #################### END OF ROS ####################



*/

// Some code that was usefull to get info in the log
//console.log(f.getGeometry().getType());
//console.log();

//py -3 -m limic serve npz graph.Denmark.npz ..\BP3_Webinterface\bachelorProject\openlayers\index.html

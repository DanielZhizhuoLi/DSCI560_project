import './style.css';
import {Map, View} from 'ol';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import { fromLonLat } from 'ol/proj';
import Feature from 'ol/Feature.js';
import Point from 'ol/geom/Point.js';
import VectorLayer from 'ol/layer/Vector.js'; 
import VectorSource from 'ol/source/Vector.js'; 
import Style from 'ol/style/Style.js';
import Icon from 'ol/style/Icon.js';
import 'ol/ol.css';


const map = new Map({
  target: 'map',
  layers: [
    new TileLayer({
      source: new OSM()
    })
  ],
  view: new View({
    center: fromLonLat([-103, 40]),
    zoom: 5
  })
});

function createMarker(lon, lat) {
  return new Feature({
    geometry: new Point(fromLonLat([lon, lat])),
  });
}

function addMarkers(locations) {
  const validLocations = locations.filter(
    (loc) =>
      loc.longitude !== null &&
      loc.latitude !== null &&
      !isNaN(parseFloat(loc.longitude)) &&
      !isNaN(parseFloat(loc.latitude))
  );

  const features = validLocations.map((location) => 
    createMarker(parseFloat(location.longitude), parseFloat(location.latitude))
  );
  
  const vectorSource = new VectorSource({
    features: features,
  }); 
  
  const vectorLayer = new VectorLayer({
    source: vectorSource,
    style: new Style({
      image: new Icon({
        anchor: [0.5, 1],
        src: 'https://cdn-icons-png.flaticon.com/128/684/684908.png',
        scale: 0.05,
      }),
    }),
  });

  map.addLayer(vectorLayer);
};



fetch('http://localhost:3000/locations')
  .then(response => response.json()) 
  .then(data => {
    console.log(data);
    addMarkers(data);
  })
  .catch(error => {
    console.error('Error fetching location data:', error);
  });
  

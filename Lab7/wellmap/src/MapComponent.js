import React, { useEffect, useState, useRef } from "react";
import "ol/ol.css";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import OSM from "ol/source/OSM";
import Feature from "ol/Feature";
import Point from "ol/geom/Point";
import { fromLonLat } from "ol/proj";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import { Icon, Style } from "ol/style";
import Overlay from "ol/Overlay";

// 🔹 Firebase REST API URL
const FIREBASE_URL = "https://wellmap-91f48-default-rtdb.firebaseio.com/.json";

const MapComponent = () => {
  const [wells, setWells] = useState([]);
  const popupRef = useRef(null);
  const closerRef = useRef(null);

  // 🔹 Fetch well data from Firebase
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(FIREBASE_URL);
        const data = await response.json();

        if (data) {
          const wellsArray = Object.values(data)
            .map((well, index) => ({
              id: well.id || index,
              name: well.name || "Unknown Well",
              lat: well.latitude !== undefined ? parseFloat(well.latitude) : null,
              lon: well.longitude !== undefined ? parseFloat(well.longitude) : null,
              api: well.api || "N/A",
              formation: well.stimulated_formation || "N/A",
              top_depth: well["top_(ft)"] || "N/A",
              bottom_depth: well["bottom_(ft)"] || "N/A",
              stages: well.stimulation_stages || "N/A",
              volume: well.volume || "N/A",
              volume_units: well.volume_units || "",
              details: well.details || "No details available",
            }))
            .filter((well) => well.lat !== null && well.lon !== null && !isNaN(well.lat) && !isNaN(well.lon));

          console.log("Processed Wells Data:", wellsArray);
          setWells(wellsArray);
        }
      } catch (error) {
        console.error("Failed to fetch data:", error);
      }
    };

    fetchData();
  }, []);

  // 🔹 Load OpenLayers map
  useEffect(() => {
    if (wells.length === 0) return;

    const map = new Map({
      target: "map",
      layers: [
        new TileLayer({
          source: new OSM(),
        }),
      ],
      view: new View({
        center: fromLonLat([-103.731825, 48.109997]), // Default center
        zoom: 6, // Adjust zoom level
      }),
    });

    console.log("Creating markers for wells:", wells);

    // 🔹 Create markers with larger icons
    const features = wells.map((well) => {
      console.log(`Adding marker for: ${well.name} at (${well.lat}, ${well.lon})`);
      const feature = new Feature({
        geometry: new Point(fromLonLat([well.lon, well.lat])),
        wellData: well,
      });

      feature.setStyle(
        new Style({
          image: new Icon({
            src: "https://maps.google.com/mapfiles/ms/icons/red-dot.png", // Large pin icon
            scale: 1.2, // Bigger marker
          }),
        })
      );

      return feature;
    });

    const vectorLayer = new VectorLayer({
      source: new VectorSource({ features }),
    });

    map.addLayer(vectorLayer);

    // 🔹 Create popup
    const overlay = new Overlay({
      element: popupRef.current,
      autoPan: true,
      autoPanAnimation: { duration: 250 },
    });

    map.addOverlay(overlay);

    if (closerRef.current) {
      closerRef.current.onclick = function () {
        overlay.setPosition(undefined);
        closerRef.current.blur();
        return false;
      };
    }

    // 🔹 Show popup when clicking on a marker
    map.on("singleclick", function (evt) {
      const feature = map.forEachFeatureAtPixel(evt.pixel, (feature) => feature);
      if (feature) {
        const coordinates = feature.getGeometry().getCoordinates();
        const well = feature.get("wellData");

        const content = document.getElementById("popup-content");
        if (content) {
          content.innerHTML = `
            <h3>${well.name}</h3>
            <table class="popup-table">
              <tr><td><strong>API:</strong></td><td>${well.api}</td><td><strong>Formation:</strong></td><td>${well.formation}</td></tr>
              <tr><td><strong>Top Depth:</strong></td><td>${well.top_depth} ft</td><td><strong>Bottom Depth:</strong></td><td>${well.bottom_depth} ft</td></tr>
              <tr><td><strong>Stages:</strong></td><td>${well.stages}</td><td><strong>Volume:</strong></td><td>${well.volume} ${well.volume_units}</td></tr>
              <tr><td><strong>Details:</strong></td><td colspan="3">${well.details}</td></tr>
            </table>
          `;
          overlay.setPosition(coordinates);
        }
      }
    });

    return () => map.setTarget(undefined);
  }, [wells]);

  return (
    <div>
      <h2>Well Locations Map</h2>
      <div id="map" style={{ width: "100%", height: "500px" }}></div>
      {/* 🔹 Popup */}
      <div ref={popupRef} id="popup" className="ol-popup">
        <a href="#" ref={closerRef} id="popup-closer" className="ol-popup-closer"></a>
        <div id="popup-content"></div>
      </div>
    </div>
  );
};

export default MapComponent;

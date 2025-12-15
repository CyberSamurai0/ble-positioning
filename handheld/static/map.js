console.log("Created for Purdue's CNIT54600 Course.\nSee https://github.com/CyberSamurai0/ble-positioning for more information.")

const MIN_ZOOM = -3;
const MAX_ZOOM = 0;
const DISABLE_ZOOM = false;
const SHOW_BEACONS = true; // TODO disable beacon markers in release
import {initBeaconMarkers} from "./beacons.js"
import {metersToPixels, pixelsToMeters, getImageDimensions} from "./helpers.js"

/***** MAP SETUP *****/

// Create a Leaflet map instance within the element with id "map"
let map = L.map("map", {
    crs: L.CRS.Simple,
    minZoom: MIN_ZOOM,
    maxZoom: MAX_ZOOM,
    zoomControl: !DISABLE_ZOOM,
});

// Use mouse movement events to track and display the mouse's live position
map.on('mousemove', e => {
    const coordinateBox = document.getElementById('coordinate-box');

    // Limit to 2 decimal places
    const lat = e.latlng.lat.toFixed(2);
    const lng = e.latlng.lng.toFixed(2);

    // Show units in meters as well
    const m_north = pixelsToMeters(e.latlng.lat).toFixed(2);
    const m_east = pixelsToMeters(e.latlng.lng).toFixed(2);

    // Set the text box content with all three values
    coordinateBox.textContent = `Coordinates: (${lat}, ${lng})\r\n` +
        `Feet: (${(e.latlng.lat/30).toFixed(2)}, ${(e.latlng.lng/30).toFixed(2)})\r\n` +
        `Meters: (${m_north}, ${m_east})`;
});

// Set the map to scale based on the source image
getImageDimensions("./floorplans/0001-04.png").then(dimensions => {
    console.log("Current floorplan image dimensions:", dimensions);

    // Define the map coordinate plane using image dimensions
    let bounds = [[0, 0], [dimensions.height, dimensions.width]];
    // Apply the floorplan image to the map
    let image = L.imageOverlay("./floorplans/0001-04.png", bounds).addTo(map)

    // Fit the map to the image dimensions
    map.fitBounds(bounds);

    // Center the map
    map.setView([dimensions.height-(dimensions.height/2), dimensions.width/2], -2);

    L.rectangle([[1600, 1318], [2930, 2100]]).addTo(map);
    L.rectangle([[3700, 3500], [2800, 4550]]).setStyle({color: "#ff0000"}).addTo(map);


});


/***** ATTEMPT TO RETRIEVE CALCULATED POSITION *****/

const SHOW_POSITION = true;

if (SHOW_POSITION) {
    let positionMarker = L.marker([0, 0]).addTo(map);

    let posHTTP = new XMLHttpRequest();
    posHTTP.onreadystatechange = () => {
        if (posHTTP.readyState === 4 && posHTTP.status === 200) {
            let posData = JSON.parse(posHTTP.responseText);
            console.log(posData);
            if (posData.hasOwnProperty("x") && posData.hasOwnProperty("y")) {
                positionMarker.setLatLng([posData.x, posData.y]);
            }
            //updateBeacons();
        }
    }

    posHTTP.open("GET", "./json", true);
    posHTTP.send();

    setInterval(() => {
        posHTTP.open("GET", "./json", true);
        posHTTP.send();
    }, 1000); // Refresh beacons every 3s
}

/***** RETRIEVE LATEST BEACON POSITIONS *****/
if (SHOW_BEACONS) initBeaconMarkers(map, "./beacons", 3000);
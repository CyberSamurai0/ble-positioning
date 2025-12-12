console.log("Created for Purdue's CNIT54600 Course.\nSee https://github.com/CyberSamurai0/ble-positioning for more information.")

const MIN_ZOOM = -3;
const MAX_ZOOM = 0;
const DISABLE_ZOOM = false;
const SHOW_BEACONS = true; // TODO disable beacon markers in release

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
    map.setView([dimensions.height-(dimensions.height/2), dimensions.width/2], -2)
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

if (SHOW_BEACONS) {
    let beaconMarkers = [];
    let beaconData = [];

    function addBeacon(lat, long) {
        let marker = L.marker([lat, long]);
        marker.addTo(map);
        beaconMarkers.push(marker);
        return marker;
    }

    function updateBeacons() {
        // Go through existing markers and update RSSI
        for (let marker of beaconMarkers) {
            // Find matching beacon in beaconData
            let match = beaconData.find(beacon => beacon["loc_north"] === marker.getLatLng().lat && beacon["loc_east"] === marker.getLatLng().lng);

            // If a match is present
            if (match) {
                // Update the popup with new RSSI value
                marker.bindPopup(`RSSI: ${match["avg_rssi"]} dBm\r\nDistance: ${match["distance"]}`);
            } else { // Stale beacon, remove it
                // Remove marker from beaconMarkers array
                let toRemove = beaconMarkers.splice(beaconMarkers.indexOf(marker))[0];
                // Remove the marker from the map
                if (toRemove instanceof L.Layer) map.removeLayer(toRemove[0]);
            }
        }

        for (let beacon of beaconData) {
            // Check if beacon is already present in beaconMarkers
            let match = beaconMarkers.find(marker => beacon["loc_north"] === marker.getLatLng().lat && beacon["loc_east"] === marker.getLatLng().lng);
            // Assume already updated if match is found
            // If no match, add a new marker
            if (!match) {
                // New beacon, add it
                if (beacon.hasOwnProperty("loc_north") && beacon.hasOwnProperty("loc_east") && beacon.hasOwnProperty("avg_rssi")) {
                    addBeacon(beacon.loc_north, beacon.loc_east).bindPopup(`RSSI: ${beacon["avg_rssi"]} dBm`);
                }
            }
        }
    }

    // Build HTTP request object that we reuse
    let beaconsHTTP = new XMLHttpRequest();
    // Callback function for request complete
    beaconsHTTP.onreadystatechange = () => {
        if (beaconsHTTP.readyState === 4 && beaconsHTTP.status === 200) {
            beaconData = JSON.parse(beaconsHTTP.responseText);
            updateBeacons();
        }
    }

    beaconsHTTP.open("GET", "./beacons", true);
    // Send a request immediately
    beaconsHTTP.send();

    // Send a request indefinitely every 3 seconds
    setInterval(() => {
        beaconsHTTP.open("GET", "./beacons", true);
        beaconsHTTP.send();
    }, 3000);
}
const MIN_ZOOM = -3;
const MAX_ZOOM = 0;
const DISABLE_ZOOM = false;
const SHOW_BEACONS = true; // TODO disable beacon markers in release

let map = L.map("map", {
    crs: L.CRS.Simple,
    minZoom: MIN_ZOOM,
    maxZoom: MAX_ZOOM,
    zoomControl: !DISABLE_ZOOM,
});

function getImageDimensions(imageURL) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            resolve({ width: img.width, height: img.height });
        }

        img.onerror = reject;
        img.src = imageURL;
    });
}

map.on('mousemove', e => {
    const coordinateBox = document.getElementById('coordinate-box');
    const lat = e.latlng.lat.toFixed(2); // Limit to 4 decimal places
    const lng = e.latlng.lng.toFixed(2);
    coordinateBox.textContent = `Coordinates: (${lat}, ${lng})\r\nFeet: (${(lat/30).toFixed(2)}, ${(lng/30).toFixed(2)})`;
});

getImageDimensions("./floorplans/0001-04.png").then(dimensions => {
    console.log("Image dimensions:", dimensions);
    
    let bounds = [[0, 0], [dimensions.height, dimensions.width]];
    let image = L.imageOverlay("./floorplans/0001-04.png", bounds).addTo(map)
    
    map.fitBounds(bounds);
    map.setView([dimensions.height-(dimensions.height/2), dimensions.width/2], -2)
});

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
        // TODO go through beaconData and compare with beaconMarkers
        // If a beacon is new, add it
        // If a beacon is gone, remove it
        // If a beacon is present, update its RSSI value

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

    let beaconsHTTP = new XMLHttpRequest();
    beaconsHTTP.onreadystatechange = () => {
        if (beaconsHTTP.readyState === 4 && beaconsHTTP.status === 200) {
            beaconData = JSON.parse(beaconsHTTP.responseText);
            console.log(beaconData);
            updateBeacons();
            console.log(beaconMarkers);
        }
    }

    beaconsHTTP.open("GET", "./beacons", true);
    beaconsHTTP.send();

    setInterval(() => {
        beaconsHTTP.open("GET", "./beacons", true);
        beaconsHTTP.send();
    }, 3000); // Refresh beacons every 3s
}
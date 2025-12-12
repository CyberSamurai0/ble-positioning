let beaconMarkers = [];
let beaconData = [];

export function initBeaconMarkers(map, url, interval) {
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

    // Send a request immediately
    beaconsHTTP.open("GET", url, true);
    beaconsHTTP.send();

    // Send a request indefinitely every 3 seconds
    setInterval(() => {
        beaconsHTTP.open("GET", url, true);
        beaconsHTTP.send();
    }, interval);
}
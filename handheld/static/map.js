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


/***** RETRIEVE LATEST BEACON POSITIONS *****/
if (SHOW_BEACONS) {
    let beacons = [];

    function addBeacon(lat, long) {
        L.marker([lat, long]).addTo(map);
    }

    function updateBeacons() {
        for (let beacon of beacons) {
            if (beacon.hasOwnProperty("loc_north") && beacon.hasOwnProperty("loc_east")) {
                addBeacon(beacon.loc_north, beacon.loc_east);
            }
        }
    }

    let beaconsHTTP = new XMLHttpRequest();
    beaconsHTTP.onreadystatechange = () => {
        if (beaconsHTTP.readyState === 4 && beaconsHTTP.status === 200) {
            beacons = JSON.parse(beaconsHTTP.responseText);
            console.log(beacons);
            updateBeacons();
        }
    }

    beaconsHTTP.open("GET", "./beacons.json", true);
    beaconsHTTP.send();

    /*setInterval(() => {
        beaconsHTTP.open("GET", "./beacons.json", true);
        beaconsHTTP.send();
    }, 5000); // Refresh beacons every 5s
    */
}
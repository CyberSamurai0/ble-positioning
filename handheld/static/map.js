const MIN_ZOOM = -3;
const MAX_ZOOM = 0;
const DISABLE_ZOOM = false;

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
export function metersToPixels(meters) {
    if (typeof meters !== "number") return;

    // With the current floorplan, 1ft=30px
    // First convert to feet, then to pixels
    return meters * 3.28084 * 30;
}

export function pixelsToMeters(px) {
    if (typeof px !== "number") return;

    // Divide by 30 and then 3.28084
    return px / 98.4252
}

export function getImageDimensions(imageURL) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            resolve({ width: img.width, height: img.height });
        }

        img.onerror = reject;
        img.src = imageURL;
    });
}
const default_map_location = {
    center: [30.314494, 59.938676],
    zoom: 8,
    duration: 1000
}

var last_shipping_method = null

initMapPromise = initMap()

async function initMap() {
    await mapManager.initMap("map", default_map_location)
    await new Promise((resolve, reject) => {
        fetch(get_routes_url)
            .then(response => response.json())
            .then(jsonData => {
                mapManager.addGeojsonToMap("map", "routes", jsonData["routes"]);
                jsonData["points"].forEach(point => {
                    mapManager.addMarker("map", point["id"], point["coordinates"], point["html"]);
                });
                resolve();
            })
            .catch(error => {
                console.error('Ошибка загрузки GeoJSON:', error);
                reject(error);
            });
    });
}
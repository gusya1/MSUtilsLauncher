
var initPromise = initYandexMap()

async function initYandexMap()
{
    await ymaps3.ready
    document.yandex_maps = {}
}



function makeMapManager() {
    function makeMarkerElement(innerHTML) {
        const markerElement = document.createElement('div');
            markerElement.innerHTML = innerHTML;
        return markerElement
    }

    return {
        async initMap(map_id, map_location) {
            await initPromise;
            const {YMap, YMapDefaultSchemeLayer, YMapDefaultFeaturesLayer} = ymaps3;
            map = new YMap(
                document.getElementById('map'),
                {
                    location: map_location
                }
            );

            document.deliveryPoint = null;

            map.addChild(new YMapDefaultSchemeLayer());
            map.addChild(new YMapDefaultFeaturesLayer({zIndex: 1801}));

            document.yandex_maps[map_id] = {
                map: map,
                childs: {}
            }
        },
        setMapCenter(map_id, location) {
            document.yandex_maps[map_id].map.setLocation(location);
        },
        addGeojsonToMap(map_id, geojson_data_id, geojsonData) {
            map = document.yandex_maps[map_id].map
            
            const {YMapFeatureDataSource, YMapLayer, YMapFeature} = ymaps3;
            const dataSource = new YMapFeatureDataSource({ 
                id: geojson_data_id
            });
            map.addChild(dataSource);
            const layer = new YMapLayer({
                source: geojson_data_id,
                type: 'features',
                zIndex: 1800, 
            })
            map.addChild(layer);

            const features = geojsonData.features;
            if (features) {
                features.forEach(featureData => {
                    const feature = new YMapFeature({
                        id: featureData.id.toString(),
                        source: geojson_data_id,
                        geometry: featureData.geometry,
                        style: featureData.style,
                        properties: featureData.properties
                    });
                    
                    map.addChild(feature);
                })
            }

            document.yandex_maps[map_id].childs[geojson_data_id] = [layer]
        },
        addMarker(map_id, marker_id, coordinates, innerHtml) {
            map = document.yandex_maps[map_id].map

            const {YMapMarker} = ymaps3;
            const marker = new YMapMarker({
                coordinates: coordinates,
            }, makeMarkerElement(innerHtml));
            map.addChild(marker);

            document.yandex_maps[map_id].childs[marker_id] = [marker]
        },
        addMarkerArray(map_id, marker_array_id, coordinates_list, innerHtml) {
            map = document.yandex_maps[map_id].map
            const {YMapMarker} = ymaps3;
            var markers = []
            coordinates_list.forEach(coordinates => {
                const marker = new YMapMarker({
                    coordinates: coordinates,
                }, makeMarkerElement(innerHtml));
                map.addChild(marker);
                markers.push(marker)
            })
            document.yandex_maps[map_id].childs[marker_array_id] = markers
        },
        hasElement(map_id, element_id) {
            return element_id in document.yandex_maps[map_id].childs
        },
        removeElement(map_id, element_id) {
            map = document.yandex_maps[map_id].map
            document.yandex_maps[map_id].childs[element_id].forEach(child => {
                map.removeChild(child);
            })
            delete document.yandex_maps[map_id].childs[element_id]
        },
        hideElement(map_id, element_id) {
            map = document.yandex_maps[map_id].map
            document.yandex_maps[map_id].childs[element_id].forEach(child => {
                map.removeChild(child);
            })
        },
        showElement(map_id, element_id) {
            map = document.yandex_maps[map_id].map
            document.yandex_maps[map_id].childs[element_id].forEach(child => {
                map.addChild(child);
            })
        }
    }
}

const mapManager = makeMapManager()
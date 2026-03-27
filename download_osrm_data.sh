#!/bin/bash
set -e

# URL для скачивания (регион Санкт-Петербург и ЛО)
URL="https://download.geofabrik.de/europe/russia/saint-petersburg-and-leningrad-oblast-latest.osm.pbf"
OUTPUT_DIR="osrm"
OUTPUT_FILE="$OUTPUT_DIR/map.osm.pbf"

echo "Скачивание OSM данных для Санкт-Петербурга и Ленинградской области..."

# Создаём папку, если её нет
mkdir -p "$OUTPUT_DIR"

# Скачиваем с помощью wget (или curl, если wget нет)
if command -v wget &> /dev/null; then
    wget -O "$OUTPUT_FILE" "$URL"
elif command -v curl &> /dev/null; then
    curl -L -o "$OUTPUT_FILE" "$URL"
else
    echo "Ошибка: ни wget, ни curl не установлены."
    exit 1
fi

echo "Файл успешно сохранён: $OUTPUT_FILE"
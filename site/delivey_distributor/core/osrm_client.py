import requests

from .data_structure import Point


def compute_time_matrix(points: list[Point]) -> list[list[float]]:
    """
    Вычисляет матрицу времени в секундах для списка точек,
    используя OSRM (http://localhost:5000).
    """
    coords = ";".join(f"{p.longitude},{p.latitude}" for p in points)
    url = f"http://localhost:5000/table/v1/driving/{coords}"
    
    response = requests.get(url)
    data = response.json()
    
    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM error: {data.get('message', 'Unknown error')}")
    
    # durations — это матрица в секундах (float)
    durations = data["durations"]

    # Убедимся, что это квадратная матрица нужного размера
    if len(durations) != len(points) or any(len(row) != len(points) for row in durations):
        raise ValueError("OSRM вернул матрицу неверного размера")
    
    return durations
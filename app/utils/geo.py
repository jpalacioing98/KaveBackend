import math

def haversine(lat1, lon1, lat2, lon2):
    # devuelve distancia en kilómetros
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def order_waypoints_by_nearest(start_lat, start_lng, waypoints):
    """
    Algoritmo greedy: siempre seleccionar el waypoint más cercano al punto actual.
    waypoints: [{'passenger_id', 'lat','lng','address'}]
    devuelve waypoints ordenados y con distancia
    """
    if start_lat is None or start_lng is None:
        # si no hay geolocalización, devuelve en orden original
        for i, w in enumerate(waypoints):
            w['distance_from_start'] = None
        return waypoints

    remaining = waypoints.copy()
    ordered = []
    cur_lat, cur_lng = start_lat, start_lng

    while remaining:
        best = min(remaining, key=lambda w: haversine(cur_lat, cur_lng, w['lat'], w['lng'] or cur_lng))
        best['distance_from_start'] = haversine(cur_lat, cur_lng, best['lat'], best['lng'])
        ordered.append(best)
        remaining.remove(best)
        cur_lat, cur_lng = best['lat'], best['lng']

    return ordered

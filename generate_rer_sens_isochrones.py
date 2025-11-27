import pandas as pd
import requests
import json
import time

# API TravelTime
APP_ID = 'f2e68f22'
API_KEY = '5b00fc23ace22919a760a2e157972075'

headers = {
    'Content-Type': 'application/json',
    'X-Application-Id': APP_ID,
    'X-Api-Key': API_KEY
}

# Coordonnées RER SENS
station_name = "RER SENS"
lat = 48.1956
lon = 3.2831

print(f"🚗 GÉNÉRATION DES ISOCHROMES 30min et 60min pour {station_name}")
print("=" * 60)
print(f"📍 Coordonnées : {lat}, {lon}")

# Charger les fichiers existants
with open('isochrones_30min.geojson', 'r') as f:
    iso_30 = json.load(f)
with open('isochrones_60min.geojson', 'r') as f:
    iso_60 = json.load(f)

# Générer les isochromes
for minutes, seconds, iso_data in [(30, 1800, iso_30), (60, 3600, iso_60)]:
    print(f"\n⏱️  Génération {minutes} min...")
    
    payload = {
        "departure_searches": [
            {
                "id": f"{station_name}_{minutes}min",
                "coords": {"lat": lat, "lng": lon},
                "departure_time": "2024-01-15T08:00:00Z",
                "travel_time": seconds,
                "transportation": {"type": "driving"}
            }
        ]
    }
    
    try:
        response = requests.post(
            'https://api.traveltimeapp.com/v4/time-map',
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            
            for result in data['results']:
                for shape in result['shapes']:
                    # Convertir les coordonnées lat/lng en format [lng, lat] pour GeoJSON
                    coordinates = [[coord['lng'], coord['lat']] for coord in shape['shell']]
                    
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "station": station_name,
                            "duration": f"{minutes}min"
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [coordinates]
                        }
                    }
                    iso_data['features'].append(feature)
            
            print(f"         ✅ {minutes} min OK")
        else:
            print(f"         ❌ {minutes} min ERREUR: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"         ❌ {minutes} min EXCEPTION: {e}")
    
    time.sleep(0.1)  # Pause courte

# Sauvegarder les fichiers
with open('isochrones_30min.geojson', 'w') as f:
    json.dump(iso_30, f, indent=2)

with open('isochrones_60min.geojson', 'w') as f:
    json.dump(iso_60, f, indent=2)

print(f"\n✅ Isochromes générés pour {station_name}")
print("✅ Fichiers mis à jour :")
print("   - isochrones_30min.geojson")
print("   - isochrones_60min.geojson")
import pandas as pd
import requests
import json
import time

# ⚠️ REMPLACE PAR TES IDENTIFIANTS TRAVELTIME
APP_ID = 'f2e68f22'
API_KEY = '5b00fc23ace22919a760a2e157972075'

headers = {
    'Content-Type': 'application/json',
    'X-Application-Id': APP_ID,
    'X-Api-Key': API_KEY
}

# Lire les stations
df = pd.read_csv('all_stations_geocoded.csv', sep=';')

# Stations à regénérer
stations_to_fix = ['ici Paris ', 'ici Creuse - Guéret']

# Charger les isochrones existants
with open('isochrones_90min.geojson', 'r') as f:
    iso_90 = json.load(f)
with open('isochrones_120min.geojson', 'r') as f:
    iso_120 = json.load(f)

print("🔄 Régénération des isochrones pour Paris et Guéret...")

for station_name in stations_to_fix:
    row = df[df['Nom_Station'] == station_name].iloc[0]
    lat = row['Latitude']
    lon = row['Longitude']
    
    print(f"\n📍 {station_name}")
    print(f"   Coordonnées : {lat}, {lon}")
    
    # Supprimer les anciens isochrones de cette station
    iso_90['features'] = [f for f in iso_90['features'] if f['properties'].get('station') != station_name]
    iso_120['features'] = [f for f in iso_120['features'] if f['properties'].get('station') != station_name]
    
    for minutes, seconds in [(90, 5400), (120, 7200)]:
        try:
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
            
            response = requests.post(
                'https://api.traveltimeapp.com/v4/time-map',
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results') and len(data['results']) > 0:
                    shapes = data['results'][0].get('shapes', [])
                    
                    for shape in shapes:
                        shell = shape.get('shell', [])
                        if shell:
                            coords = [[point['lng'], point['lat']] for point in shell]
                            coords.append(coords[0])
                            
                            feature = {
                                "type": "Feature",
                                "properties": {
                                    "station": station_name,
                                    "time": f"{minutes} min"
                                },
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [coords]
                                }
                            }
                            
                            if minutes == 90:
                                iso_90['features'].append(feature)
                            else:
                                iso_120['features'].append(feature)
                    
                    print(f"   ✅ {minutes} min OK")
            else:
                print(f"   ❌ {minutes} min - Erreur {response.status_code}")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ {minutes} min - Erreur: {str(e)[:60]}")

# Sauvegarder
with open('isochrones_90min.geojson', 'w') as f:
    json.dump(iso_90, f)
with open('isochrones_120min.geojson', 'w') as f:
    json.dump(iso_120, f)

print("\n✅ Isochrones 90min et 120min mis à jour !")
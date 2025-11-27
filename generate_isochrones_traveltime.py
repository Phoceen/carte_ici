import pandas as pd
import requests
import json
import time

# ⚠️ REMPLACE PAR TES IDENTIFIANTS
APP_ID = 'f2e68f22'
API_KEY = '5b00fc23ace22919a760a2e157972075'

# Headers pour l'API
headers = {
    'Content-Type': 'application/json',
    'X-Application-Id': APP_ID,
    'X-Api-Key': API_KEY
}

# Lire les stations
df = pd.read_csv('all_stations_geocoded.csv', sep=';')

print("🚗 GÉNÉRATION DES ISOCHRONES 1h30 et 2h (TravelTime API)")
print("=" * 60)

features_90min = []
features_120min = []

for idx, row in df.iterrows():
    station = row['Nom_Station']
    lat = row['Latitude']
    lon = row['Longitude']
    
    print(f"{idx+1}/{len(df)} - {station}...")
    
    # Requête pour 90 min (5400 sec) et 120 min (7200 sec)
    for minutes, seconds in [(90, 5400), (120, 7200)]:
        try:
            payload = {
                "departure_searches": [
                    {
                        "id": f"{station}_{minutes}min",
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
                
                # Extraire les coordonnées du polygone
                if data.get('results') and len(data['results']) > 0:
                    shapes = data['results'][0].get('shapes', [])
                    
                    for shape in shapes:
                        shell = shape.get('shell', [])
                        if shell:
                            # Convertir en format GeoJSON [lon, lat]
                            coords = [[point['lng'], point['lat']] for point in shell]
                            coords.append(coords[0])  # Fermer le polygone
                            
                            feature = {
                                "type": "Feature",
                                "properties": {
                                    "station": station,
                                    "time": f"{minutes} min"
                                },
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [coords]
                                }
                            }
                            
                            if minutes == 90:
                                features_90min.append(feature)
                            else:
                                features_120min.append(feature)
                    
                    print(f"         ✅ {minutes} min OK")
                else:
                    print(f"         ⚠️ {minutes} min - Pas de résultat")
            else:
                print(f"         ❌ {minutes} min - Erreur {response.status_code}: {response.text[:80]}")
        
        except Exception as e:
            print(f"         ❌ {minutes} min - Erreur: {str(e)[:60]}")
        
        # Pause pour respecter les limites
        time.sleep(0.5)

print("\n" + "=" * 60)
print(f"✅ Isochrones 90 min : {len(features_90min)}")
print(f"✅ Isochrones 120 min : {len(features_120min)}")

# Sauvegarder en GeoJSON
with open('isochrones_90min.geojson', 'w') as f:
    json.dump({"type": "FeatureCollection", "features": features_90min}, f)

with open('isochrones_120min.geojson', 'w') as f:
    json.dump({"type": "FeatureCollection", "features": features_120min}, f)

print("\n✅ Fichiers sauvegardés :")
print("   - isochrones_90min.geojson")
print("   - isochrones_120min.geojson")
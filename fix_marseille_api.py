import requests
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Configuration TravelTime API
APP_ID = os.getenv('TRAVELTIME_APP_ID')
API_KEY = os.getenv('TRAVELTIME_API_KEY')
BASE_URL = 'https://api.traveltimeapp.com/v4/time-map'

def generate_isochrone_traveltime_v2(lat, lon, duration_minutes, station_name):
    """Generate isochrone using TravelTime API with corrected parameters"""
    headers = {
        'X-Application-Id': APP_ID,
        'X-Api-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Utiliser departure_time pour éviter les erreurs de validation
    data = {
        "departure_searches": [
            {
                "id": f"isochrone_{duration_minutes}min_{station_name.replace(' ', '_')}",
                "coords": {
                    "lat": lat,
                    "lng": lon
                },
                "transportation": {
                    "type": "driving"
                },
                "travel_time": duration_minutes * 60,
                "departure_time": "2025-11-27T14:00:00Z",  # Heure fixe pour éviter les erreurs
                "level_of_detail": {
                    "scale_type": "simple",
                    "level": "lowest"
                }
            }
        ]
    }
    
    print(f"  Génération isochrone {duration_minutes}min pour {station_name}...")
    print(f"    Coordonnées: {lat}, {lon}")
    print(f"    Travel time: {duration_minutes * 60} seconds")
    
    try:
        response = requests.post(BASE_URL, headers=headers, json=data, timeout=30)
        
        print(f"    Status code: {response.status_code}")
        
        if response.status_code == 422:
            print(f"    Response: {response.text}")
            return None
            
        response.raise_for_status()
        result = response.json()
        
        if 'results' in result and len(result['results']) > 0:
            shapes = result['results'][0]['shapes']
            if len(shapes) > 0:
                coordinates = shapes[0]['shell']
                print(f"    ✅ Isochrone généré avec {len(coordinates)} points")
                return coordinates
            else:
                print(f"    ⚠️  Aucune forme trouvée pour {station_name} {duration_minutes}min")
                return None
        else:
            print(f"    ❌ Pas de résultats dans la réponse")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Erreur API: {e}")
        return None

def replace_marseille_isochrone_in_file(filename, duration_minutes, new_coordinates, station_coords):
    """Replace Marseille isochrone in the specified GeoJSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    marseille_found = False
    original_count = len(data['features'])
    
    # Find and replace Marseille isochrone
    for i, feature in enumerate(data['features']):
        station = feature['properties'].get('station', '')
        
        if 'marseille' in station.lower():
            print(f"    Remplacement isochrone index {i} dans {filename}")
            
            # Update geometry with new TravelTime API coordinates
            feature['geometry'] = {
                "type": "Polygon",
                "coordinates": [new_coordinates]
            }
            
            # Update properties with correct metadata
            feature['properties'].update({
                'duration': str(duration_minutes),
                'station': 'Bureau MARSEILLE',
                'ville': 'MARSEILLE',
                'adresse': "98 RUE DE L'EVECHE 13002 MARSEILLE",
                'generated_at': datetime.now().isoformat(),
                'coordinates': f'{station_coords[0]},{station_coords[1]}'
            })
            
            marseille_found = True
            break
    
    if not marseille_found:
        print(f"    ⚠️  Aucun isochrone Marseille trouvé dans {filename}")
        return False
    
    # Save updated file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    
    final_count = len(data['features'])
    print(f"    ✅ {filename} mis à jour ({original_count} -> {final_count} features)")
    return True

def main():
    print("🔧 Régénération complète des isochrones TravelTime pour Bureau MARSEILLE")
    
    # Coordonnées exactes du Bureau MARSEILLE
    marseille_lat = 43.30211231564736
    marseille_lon = 5.367328293835255
    
    print(f"📍 Coordonnées Bureau MARSEILLE: {marseille_lat}, {marseille_lon}")
    
    # Test de connectivité API
    print(f"\n🔌 Test connectivité API...")
    try:
        test_response = requests.get("https://api.traveltimeapp.com/", timeout=10)
        print(f"    API accessible (status: {test_response.status_code})")
    except Exception as e:
        print(f"    ⚠️  Problème de connectivité: {e}")
    
    # Durées à régénérer (60, 90, 120 min)
    durations_to_fix = [60, 90, 120]
    filenames = {
        60: 'isochrones_60min.geojson',
        90: 'isochrones_90min.geojson', 
        120: 'isochrones_120min.geojson'
    }
    
    success_count = 0
    
    for duration in durations_to_fix:
        print(f"\n⏱️  Génération isochrone {duration} minutes...")
        
        # Generate new isochrone with TravelTime API
        coordinates = generate_isochrone_traveltime_v2(
            marseille_lat, marseille_lon, duration, "Bureau MARSEILLE"
        )
        
        if coordinates and len(coordinates) > 3:  # Au moins 3 points pour un polygone valide
            print(f"    Isochrone généré: {len(coordinates)} coordonnées")
            
            # Update the corresponding GeoJSON file
            success = replace_marseille_isochrone_in_file(
                filenames[duration], 
                duration, 
                coordinates, 
                (marseille_lat, marseille_lon)
            )
            
            if success:
                success_count += 1
                print(f"    ✅ Isochrone {duration}min régénéré avec succès")
            else:
                print(f"    ❌ Échec de la mise à jour pour {duration}min")
        else:
            print(f"    ❌ Impossible de générer l'isochrone {duration}min")
            # Essayer avec des paramètres différents
            print(f"    Tentative avec paramètres simplifiés...")
            
    print(f"\n🎯 Régénération terminée: {success_count}/{len(durations_to_fix)} isochrones mis à jour")
    
    if success_count > 0:
        print(f"✅ Régénérez maintenant la carte avec: python create_final_map_v2.py")
    else:
        print(f"❌ Aucun isochrone n'a pu être régénéré - vérifiez les logs d'erreur ci-dessus")

if __name__ == "__main__":
    main()
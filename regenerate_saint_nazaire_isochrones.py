#!/usr/bin/env python3
"""
Script pour régénérer uniquement les isochrones de Saint-Nazaire
avec les coordonnées corrigées
"""

import pandas as pd
import openrouteservice
import json
import time

# Configuration
ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImI0OTBkZjY4MTVmMzQwMjk4MzQwY2NiYTNiYjExMmZjIiwiaCI6Im11cm11cjY0In0='
STATIONS_FILE = 'Clean_data/stations_updated_coordinates.csv'

def regenerate_saint_nazaire_isochrones():
    """Régénère uniquement les isochrones de Saint-Nazaire"""
    
    print("🎯 RÉGÉNÉRATION DES ISOCHRONES SAINT-NAZAIRE")
    print("=" * 50)
    
    # Charger les stations
    df = pd.read_csv(STATIONS_FILE, sep=';')
    saint_nazaire = df[df['Nom_Station'] == 'RER SAINT-NAZAIRE']
    
    if saint_nazaire.empty:
        print("❌ Station RER SAINT-NAZAIRE non trouvée")
        return
        
    row = saint_nazaire.iloc[0]
    lat = row['Latitude']
    lon = row['Longitude']
    
    print(f"📍 Station: {row['Nom_Station']}")
    print(f"📍 Nouvelles coordonnées: {lat}, {lon}")
    print(f"📍 Territoire: {row['Territoire']}")
    
    # Initialiser le client OpenRouteService
    client = openrouteservice.Client(key=ORS_API_KEY)
    
    # Durées à générer
    durations = [30, 60]  # minutes
    
    for duration in durations:
        print(f"\n🚀 Génération isochrone {duration}min...")
        
        try:
            # Générer l'isochrone
            coords = [lon, lat]  # ORS attend lon, lat
            response = client.isochrones(
                locations=[coords],
                profile='driving-car',
                range=[duration * 60],  # Conversion en secondes
                interval=1800,  # Intervalle de 30 min
                units='m'
            )
            
            # Charger le fichier existant
            rer_filename = f'Clean_data/isochrones_{duration}min_rer.geojson'
            
            try:
                with open(rer_filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                print(f"❌ Fichier {rer_filename} non trouvé")
                continue
            
            # Supprimer l'ancien isochrone de Saint-Nazaire s'il existe
            existing_data['features'] = [
                feature for feature in existing_data['features']
                if feature.get('properties', {}).get('station_name') != 'RER SAINT-NAZAIRE'
            ]
            
            # Ajouter le nouvel isochrone
            for feature in response['features']:
                # Enrichir avec métadonnées
                feature['properties'].update({
                    'station_name': 'RER SAINT-NAZAIRE',
                    'station_type': 'RER',
                    'territoire': row['Territoire'],
                    'duration_minutes': duration,
                    'station_lat': lat,
                    'station_lon': lon,
                    'color': '#d7301f' if duration == 30 else '#fdae61'  # Couleurs RER
                })
                existing_data['features'].append(feature)
            
            # Sauvegarder le fichier mis à jour
            with open(rer_filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ Isochrone {duration}min mis à jour dans {rer_filename}")
            
        except Exception as e:
            print(f"   ❌ Erreur génération {duration}min: {e}")
        
        # Délai entre requêtes
        time.sleep(3)
    
    print("\n" + "=" * 50)
    print("🎉 RÉGÉNÉRATION SAINT-NAZAIRE TERMINÉE!")
    print("\n💡 Prochaines étapes:")
    print("   1. Vérifiez les fichiers Clean_data/isochrones_*min_rer.geojson")
    print("   2. Régénérez la carte finale: python create_final_map_v2.py")

if __name__ == "__main__":
    regenerate_saint_nazaire_isochrones()
#!/usr/bin/env python3
"""
Script pour mettre à jour les coordonnées avec Google Maps et générer tous les isochrones
"""

import pandas as pd
import requests
import json
import time
import os
from typing import Dict, List, Tuple

# Configuration OpenRouteService
ORS_API_KEY = "5b3ce3597851110001cf6248e95b9fff6a0e429497c64a86b89c1b8e"  # Remplacez par votre clé
ORS_BASE_URL = "https://api.openrouteservice.org/v2/isochrones/driving-car"

class IsochroneGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = ORS_BASE_URL
        
    def generate_isochrone(self, lat: float, lon: float, duration_minutes: int) -> dict:
        """Génère un isochrone pour une station donnée"""
        
        headers = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization': self.api_key,
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        body = {
            "locations": [[lon, lat]],  # ORS attend lon, lat
            "range": [duration_minutes * 60],  # Conversion en secondes
            "range_type": "time",
            "units": "m"
        }
        
        try:
            response = requests.post(self.base_url, json=body, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erreur API ORS ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur de requête: {e}")
            return None
    
    def generate_isochrones_for_stations(self, stations_df: pd.DataFrame, duration_minutes: int, 
                                       output_file: str, station_types: List[str] = None) -> bool:
        """Génère les isochrones pour un groupe de stations"""
        
        if station_types:
            filtered_df = stations_df[stations_df['Type'].isin(station_types)]
        else:
            filtered_df = stations_df
        
        print(f"🚀 Génération des isochrones {duration_minutes}min pour {len(filtered_df)} stations ({', '.join(station_types or ['toutes'])})")
        
        features = []
        success_count = 0
        error_count = 0
        
        for index, row in filtered_df.iterrows():
            station_name = row['Nom_Station']
            # Utiliser les coordonnées Google Maps si disponibles, sinon les anciennes
            lat = row.get('google_lat', row.get('Latitude'))
            lon = row.get('google_lon', row.get('Longitude'))
            
            print(f"  [{index+1}/{len(filtered_df)}] {station_name}")
            
            isochrone_data = self.generate_isochrone(lat, lon, duration_minutes)
            
            if isochrone_data and 'features' in isochrone_data:
                for feature in isochrone_data['features']:
                    # Ajouter les métadonnées de la station
                    feature['properties'].update({
                        'station_name': station_name,
                        'station_type': row['Type'],
                        'territoire': row.get('Territoire', ''),
                        'duration_minutes': duration_minutes,
                        'station_lat': lat,
                        'station_lon': lon
                    })
                    features.append(feature)
                success_count += 1
                print(f"    ✅ Succès")
            else:
                error_count += 1
                print(f"    ❌ Échec")
            
            # Délai pour respecter les limites API
            time.sleep(1)
        
        # Créer le GeoJSON final
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "duration_minutes": duration_minutes,
                "station_types": station_types or ["all"],
                "generated_at": pd.Timestamp.now().isoformat(),
                "total_stations": len(filtered_df),
                "success_count": success_count,
                "error_count": error_count
            }
        }
        
        # Créer le dossier s'il n'existe pas
        os.makedirs("Clean_data", exist_ok=True)
        
        # Sauvegarder
        output_path = os.path.join("Clean_data", output_file)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ Sauvegardé: {output_path}")
            print(f"  📊 Statistiques: {success_count} succès, {error_count} erreurs")
            return True
            
        except Exception as e:
            print(f"  ❌ Erreur de sauvegarde: {e}")
            return False

def update_station_coordinates():
    """Met à jour le fichier principal avec les coordonnées Google Maps"""
    
    print("🔄 Mise à jour des coordonnées principales...")
    
    # Charger les données originales et Google Maps
    try:
        original_df = pd.read_csv("Clean_data/stations_geocoded_clean.csv", sep=';')
        google_df = pd.read_csv("stations_google_geocoded.csv")
        
        print(f"✅ Données chargées: {len(original_df)} stations originales, {len(google_df)} stations Google")
        
        # Mettre à jour les coordonnées
        for index, row in google_df.iterrows():
            station_name = row['Nom_Station']
            if pd.notna(row['google_lat']) and pd.notna(row['google_lon']):
                # Trouver la ligne correspondante dans le DataFrame original
                mask = original_df['Nom_Station'] == station_name
                if mask.any():
                    original_df.loc[mask, 'Latitude'] = row['google_lat']
                    original_df.loc[mask, 'Longitude'] = row['google_lon']
                    print(f"  ✅ {station_name}: {row['google_lat']:.6f}, {row['google_lon']:.6f}")
        
        # Sauvegarder le fichier mis à jour
        output_path = "Clean_data/stations_updated_coordinates.csv"
        original_df.to_csv(output_path, sep=';', index=False)
        print(f"✅ Coordonnées mises à jour sauvegardées: {output_path}")
        
        return original_df
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        return None

def main():
    """Fonction principale"""
    
    print("🗺️  MISE À JOUR DES COORDONNÉES ET GÉNÉRATION DES ISOCHRONES")
    print("=" * 70)
    
    # 1. Mettre à jour les coordonnées
    stations_df = update_station_coordinates()
    if stations_df is None:
        return
    
    # 2. Initialiser le générateur d'isochrones
    generator = IsochroneGenerator(ORS_API_KEY)
    
    # 3. Configuration des générations
    durations = [30, 60, 90, 120]  # minutes
    station_configs = [
        {
            'types': ['ICI'],
            'name': 'stations',
            'description': 'stations ICI'
        },
        {
            'types': ['RER'],
            'name': 'rer',
            'description': 'stations RER'
        },
        {
            'types': ['Bureau'],
            'name': 'bureaux',
            'description': 'bureaux'
        }
    ]
    
    print(f"\n📋 PLAN DE GÉNÉRATION:")
    print(f"   - {len(durations)} durées: {durations} minutes")
    print(f"   - {len(station_configs)} types de stations")
    print(f"   - Total: {len(durations) * len(station_configs)} fichiers à générer")
    print()
    
    # 4. Générer tous les isochrones
    total_files = len(durations) * len(station_configs)
    current_file = 0
    successful_files = 0
    
    for config in station_configs:
        for duration in durations:
            current_file += 1
            
            print(f"\n[{current_file}/{total_files}] ═══════════════════════════════════════")
            
            filename = f"isochrones_{duration}min_{config['name']}.geojson"
            
            success = generator.generate_isochrones_for_stations(
                stations_df=stations_df,
                duration_minutes=duration,
                output_file=filename,
                station_types=config['types']
            )
            
            if success:
                successful_files += 1
                print(f"✅ {filename} généré avec succès")
            else:
                print(f"❌ Échec de génération de {filename}")
            
            print()
    
    # 5. Résumé final
    print("=" * 70)
    print(f"🎉 GÉNÉRATION TERMINÉE!")
    print(f"   Fichiers générés avec succès: {successful_files}/{total_files}")
    print(f"   Dossier de sortie: Clean_data/")
    print()
    print(f"📁 FICHIERS CRÉÉS:")
    
    for config in station_configs:
        for duration in durations:
            filename = f"isochrones_{duration}min_{config['name']}.geojson"
            filepath = f"Clean_data/{filename}"
            if os.path.exists(filepath):
                size_kb = os.path.getsize(filepath) / 1024
                print(f"   ✅ {filename} ({size_kb:.1f} KB)")
            else:
                print(f"   ❌ {filename} (manquant)")
    
    print(f"\n💡 Vous pouvez maintenant utiliser ces fichiers dans vos scripts de mapping!")
    print(f"   Exemple: python create_final_map_v2.py")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script optimisé pour générer les isochrones 30min et 60min 
avec les coordonnées Google Maps précises
"""

import pandas as pd
import folium
import openrouteservice
import time
import requests
import json
import geopandas as gpd
from shapely.geometry import shape
from folium.plugins import Geocoder
import os

# Configuration
ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImI0OTBkZjY4MTVmMzQwMjk4MzQwY2NiYTNiYjExMmZjIiwiaCI6Im11cm11cjY0In0='
STATIONS_FILE = 'Clean_data/stations_updated_coordinates.csv'

# Couleurs par type
COLORS = {
    'ICI': ['#2b8cbe', '#045a8d'],      # Bleu clair → foncé  
    'RER': ['#d7301f', '#fdae61'],      # Rouge → orange
    'Bureau': ['#238b45', '#006837']    # Vert clair → foncé
}

class IsochroneGeneratorOptimized:
    def __init__(self, api_key: str):
        self.client = openrouteservice.Client(key=api_key)
        self.delays = 3  # Délai entre requêtes en secondes
        
    def load_stations(self) -> pd.DataFrame:
        """Charge les stations avec coordonnées Google Maps précises"""
        try:
            df = pd.read_csv(STATIONS_FILE, sep=';')
            print(f"✅ {len(df)} stations chargées depuis {STATIONS_FILE}")
            return df
        except Exception as e:
            print(f"❌ Erreur de chargement: {e}")
            return None
    
    def generate_isochrones_by_type(self, stations_df: pd.DataFrame, station_type: str, 
                                  durations: list = [30, 60]) -> dict:
        """Génère les isochrones pour un type de station donné"""
        
        # Filtrer par type
        filtered_df = stations_df[stations_df['Type'] == station_type]
        colors = COLORS.get(station_type, ['#666666', '#333333'])
        
        print(f"\n🚀 Génération isochrones {station_type}: {len(filtered_df)} stations")
        print(f"   Durées: {durations} minutes")
        
        results = {duration: [] for duration in durations}
        
        for index, row in filtered_df.iterrows():
            station_name = row['Nom_Station']
            lat = row['Latitude']
            lon = row['Longitude']
            
            print(f"   [{index+1}/{len(filtered_df)}] {station_name}")
            
            try:
                # Appel API OpenRouteService
                coords = [lon, lat]  # ORS attend lon, lat
                response = self.client.isochrones(
                    locations=[coords],
                    profile='driving-car',
                    range=[duration * 60 for duration in durations],  # Conversion en secondes
                    interval=1800,  # Intervalle de 30 min
                    units='m'
                )
                
                # Traitement des résultats par durée
                for i, feature in enumerate(response['features']):
                    duration = durations[i] if i < len(durations) else durations[-1]
                    
                    # Enrichir avec métadonnées
                    feature['properties'].update({
                        'station_name': station_name,
                        'station_type': station_type,
                        'territoire': row.get('Territoire', ''),
                        'duration_minutes': duration,
                        'station_lat': lat,
                        'station_lon': lon,
                        'color': colors[i] if i < len(colors) else colors[-1]
                    })
                    
                    results[duration].append(feature)
                
                print(f"      ✅ Succès")
                
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
            
            # Délai respectueux de l'API
            time.sleep(self.delays)
        
        return results
    
    def save_geojson_by_duration(self, results: dict, station_type: str) -> bool:
        """Sauvegarde les GeoJSON par durée"""
        
        success_count = 0
        
        for duration, features in results.items():
            if not features:
                print(f"   ⚠️  Aucun isochrone {duration}min pour {station_type}")
                continue
                
            # Créer le GeoJSON
            geojson = {
                "type": "FeatureCollection",
                "features": features,
                "metadata": {
                    "duration_minutes": duration,
                    "station_type": station_type,
                    "generated_at": pd.Timestamp.now().isoformat(),
                    "total_features": len(features)
                }
            }
            
            # Nom de fichier selon votre demande
            type_name = station_type.lower() if station_type != 'ICI' else 'stations'
            if station_type == 'Bureau':
                type_name = 'bureaux'
            elif station_type == 'RER':
                type_name = 'rer'
                
            filename = f"isochrones_{duration}min_{type_name}.geojson"
            filepath = os.path.join("Clean_data", filename)
            
            try:
                # Créer le dossier s'il n'existe pas
                os.makedirs("Clean_data", exist_ok=True)
                
                # Sauvegarder
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(geojson, f, ensure_ascii=False, indent=2)
                
                file_size = os.path.getsize(filepath) / 1024
                print(f"   ✅ {filename} ({file_size:.1f} KB)")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Erreur sauvegarde {filename}: {e}")
        
        return success_count > 0
    
    def create_visualization_map(self, stations_df: pd.DataFrame) -> bool:
        """Crée une carte de visualisation avec tous les isochrones"""
        
        print("\n🗺️  Création de la carte de visualisation...")
        
        # Initialiser la carte
        m = folium.Map(location=(46.603, 1.888), zoom_start=6)
        Geocoder(collapsed=False).add_to(m)
        
        # Ajouter les régions françaises
        try:
            url = "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"
            geojson_data = requests.get(url).json()
            
            folium.GeoJson(
                geojson_data,
                name="Régions",
                style_function=lambda feature: {
                    'fillColor': 'grey',
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.1,
                },
                tooltip=folium.GeoJsonTooltip(fields=["nom"], aliases=["Région :"])
            ).add_to(m)
        except:
            print("   ⚠️  Impossible de charger les régions françaises")
        
        # Ajouter les stations et isochrones par type
        for station_type in ['ICI', 'RER', 'Bureau']:
            filtered_df = stations_df[stations_df['Type'] == station_type]
            colors = COLORS.get(station_type, ['#666666', '#333333'])
            
            # Groupe de calques pour ce type
            fg = folium.FeatureGroup(name=f"{station_type} ({len(filtered_df)} stations)").add_to(m)
            
            for _, row in filtered_df.iterrows():
                # Marqueurs des stations
                icon_color = 'blue' if station_type == 'ICI' else ('orange' if station_type == 'RER' else 'green')
                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=row['Nom_Station'],
                    tooltip=row['Nom_Station'],
                    icon=folium.Icon(color=icon_color)
                ).add_to(fg)
        
        # Contrôles de couches
        folium.LayerControl().add_to(m)
        
        # Sauvegarder
        try:
            m.save("carte_isochrones_preview.html")
            print("   ✅ Carte sauvegardée: carte_isochrones_preview.html")
            return True
        except Exception as e:
            print(f"   ❌ Erreur sauvegarde carte: {e}")
            return False

def main():
    """Fonction principale"""
    
    print("🎯 GÉNÉRATION OPTIMISÉE DES ISOCHRONES")
    print("=" * 50)
    
    # Initialiser le générateur
    generator = IsochroneGeneratorOptimized(ORS_API_KEY)
    
    # Charger les stations avec coordonnées Google Maps
    stations_df = generator.load_stations()
    if stations_df is None:
        return
    
    # Configuration des générations
    durations = [30, 60]  # minutes
    station_types = ['ICI', 'RER', 'Bureau']
    
    print(f"\n📋 PLAN DE GÉNÉRATION:")
    print(f"   - Durées: {durations} minutes")
    print(f"   - Types: {station_types}")
    print(f"   - Total fichiers: {len(durations) * len(station_types)}")
    
    # Générer par type de station
    all_success = True
    
    for station_type in station_types:
        print(f"\n{'='*50}")
        
        # Générer les isochrones
        results = generator.generate_isochrones_by_type(
            stations_df, station_type, durations
        )
        
        # Sauvegarder les GeoJSON
        success = generator.save_geojson_by_duration(results, station_type)
        all_success = all_success and success
    
    # Créer la carte de prévisualisation
    print(f"\n{'='*50}")
    generator.create_visualization_map(stations_df)
    
    # Résumé final
    print(f"\n{'='*50}")
    print("🎉 GÉNÉRATION TERMINÉE!")
    print(f"   Status: {'✅ Succès' if all_success else '⚠️  Partiel'}")
    
    print(f"\n📁 FICHIERS GÉNÉRÉS:")
    for station_type in station_types:
        type_name = station_type.lower() if station_type != 'ICI' else 'stations'
        if station_type == 'Bureau':
            type_name = 'bureaux'
        elif station_type == 'RER':
            type_name = 'rer'
            
        for duration in durations:
            filename = f"Clean_data/isochrones_{duration}min_{type_name}.geojson"
            if os.path.exists(filename):
                size_kb = os.path.getsize(filename) / 1024
                print(f"   ✅ isochrones_{duration}min_{type_name}.geojson ({size_kb:.1f} KB)")
            else:
                print(f"   ❌ isochrones_{duration}min_{type_name}.geojson (manquant)")
    
    print(f"\n💡 Prochaines étapes:")
    print(f"   1. Vérifiez les fichiers dans Clean_data/")
    print(f"   2. Consultez carte_isochrones_preview.html")
    print(f"   3. Utilisez python create_final_map_v2.py pour la carte finale")

if __name__ == "__main__":
    main()
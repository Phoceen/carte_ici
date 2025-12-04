#!/usr/bin/env python3
"""
Script pour géocoder les stations Radio France avec l'API Google Maps
Offre une précision bien supérieure à Nominatim pour les adresses françaises
"""

import pandas as pd
import requests
import time
import json
from typing import Tuple, Optional

# CONFIGURATION
GOOGLE_MAPS_API_KEY = "AIzaSyACMXAnYifulTyyog5hVGdKn03OplZLo5U"  # Remplacez par votre clé API
INPUT_FILE = "Clean_data/stations_geocoded_clean.csv"
OUTPUT_FILE = "stations_google_geocoded.csv"
BACKUP_FILE = "stations_google_geocoded_backup.csv"

# Délai entre les requêtes (recommandé pour éviter les limitations de taux)
REQUEST_DELAY = 0.1  # 100ms entre chaque requête

class GoogleMapsGeocoder:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.session = requests.Session()
        
    def geocode_address(self, address: str) -> Tuple[Optional[float], Optional[float], str]:
        """
        Géocode une adresse avec l'API Google Maps
        
        Returns:
            Tuple[lat, lon, status] où status peut être:
            - 'OK': succès
            - 'ZERO_RESULTS': aucun résultat
            - 'OVER_QUERY_LIMIT': limite de requêtes atteinte
            - 'REQUEST_DENIED': clé API invalide
            - 'ERROR': erreur technique
        """
        params = {
            'address': address,
            'key': self.api_key,
            'language': 'fr',
            'region': 'fr',
            'components': 'country:FR'  # Restriction à la France
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == 'OK' and len(data['results']) > 0:
                location = data['results'][0]['geometry']['location']
                return location['lat'], location['lng'], 'OK'
            else:
                return None, None, data['status']
                
        except requests.exceptions.RequestException as e:
            print(f"Erreur de requête pour '{address}': {e}")
            return None, None, 'ERROR'
        except Exception as e:
            print(f"Erreur inattendue pour '{address}': {e}")
            return None, None, 'ERROR'

def main():
    # Vérification de la clé API
    if GOOGLE_MAPS_API_KEY == "VOTRE_CLE_API_ICI":
        print("❌ ERREUR: Veuillez remplacer VOTRE_CLE_API_ICI par votre vraie clé API Google Maps")
        print("Modifiez la ligne 15 du fichier geocode_google_maps.py")
        return
    
    # Chargement des données
    print("📁 Chargement des données...")
    try:
        df = pd.read_csv(INPUT_FILE, sep=';')
        print(f"✅ {len(df)} stations chargées depuis {INPUT_FILE}")
    except FileNotFoundError:
        print(f"❌ ERREUR: Fichier {INPUT_FILE} non trouvé")
        return
    except Exception as e:
        print(f"❌ ERREUR lors du chargement: {e}")
        return
    
    # Initialisation du géocodeur
    geocoder = GoogleMapsGeocoder(GOOGLE_MAPS_API_KEY)
    
    # Ajout des colonnes pour les résultats Google Maps
    df['google_lat'] = None
    df['google_lon'] = None
    df['google_status'] = None
    
    # Statistiques
    total_stations = len(df)
    processed = 0
    success = 0
    errors = 0
    
    print(f"\n🚀 Début du géocodage de {total_stations} stations...")
    print("=" * 50)
    
    for index, row in df.iterrows():
        processed += 1
        station_name = row['Nom_Station']
        address = row['Adresse']
        
        print(f"[{processed}/{total_stations}] {station_name}")
        print(f"   Adresse: {address}")
        
        # Géocodage
        lat, lon, status = geocoder.geocode_address(address)
        
        # Sauvegarde des résultats
        df.at[index, 'google_lat'] = lat
        df.at[index, 'google_lon'] = lon
        df.at[index, 'google_status'] = status
        
        if status == 'OK':
            success += 1
            print(f"   ✅ Succès: {lat:.6f}, {lon:.6f}")
        elif status == 'ZERO_RESULTS':
            errors += 1
            print(f"   ⚠️  Aucun résultat trouvé")
        elif status == 'OVER_QUERY_LIMIT':
            print(f"   🚫 Limite de requêtes atteinte. Arrêt du traitement.")
            break
        elif status == 'REQUEST_DENIED':
            print(f"   🚫 Requête refusée. Vérifiez votre clé API.")
            break
        else:
            errors += 1
            print(f"   ❌ Erreur: {status}")
        
        # Sauvegarde intermédiaire tous les 10 enregistrements
        if processed % 10 == 0:
            df.to_csv(BACKUP_FILE, index=False)
            print(f"   💾 Sauvegarde intermédiaire effectuée")
        
        # Délai entre les requêtes
        time.sleep(REQUEST_DELAY)
        print()
    
    # Sauvegarde finale
    print("=" * 50)
    print("💾 Sauvegarde des résultats...")
    
    try:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"✅ Résultats sauvegardés dans {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ ERREUR lors de la sauvegarde: {e}")
        return
    
    # Statistiques finales
    print("\n📊 STATISTIQUES FINALES:")
    print(f"   Total traité: {processed}/{total_stations}")
    print(f"   Succès: {success} ({success/processed*100:.1f}%)")
    print(f"   Erreurs: {errors} ({errors/processed*100:.1f}%)")
    
    # Analyse des erreurs
    if errors > 0:
        print(f"\n🔍 ANALYSE DES ERREURS:")
        error_stations = df[df['google_status'] != 'OK']
        for _, row in error_stations.iterrows():
            print(f"   - {row['Nom_Station']}: {row['google_status']}")
    
    print(f"\n🎉 Géocodage terminé ! Consultez le fichier {OUTPUT_FILE}")
    print("💡 Conseil: Comparez les coordonnées Google avec celles de Nominatim pour voir la différence de précision")

if __name__ == "__main__":
    main()
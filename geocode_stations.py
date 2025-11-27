import pandas as pd
from geopy.geocoders import Nominatim
import time

# Lire le fichier fusionné
df = pd.read_csv('all_stations.csv', sep=';')

# Initialiser le géocodeur (gratuit, pas de clé API nécessaire)
geolocator = Nominatim(user_agent="carte_ici_projet")

# Fonction de géocodage
def geocode_address(address):
    try:
        time.sleep(1)  # Respecter les limites d'utilisation (1 req/sec)
        location = geolocator.geocode(address + ", France")
        if location:
            return location.latitude, location.longitude
        else:
            print(f"   ⚠️  Pas trouvé : {address}")
            return None, None
    except Exception as e:
        print(f"   ❌ Erreur pour {address}: {e}")
        return None, None

# Géocoder toutes les adresses
print("🌍 GÉOCODAGE EN COURS... (ça va prendre 1-2 minutes)")
print("=" * 60)

latitudes = []
longitudes = []

for idx, row in df.iterrows():
    station = row['Nom_Station']
    address = row['Adresse']
    
    print(f"{idx+1}/{len(df)} - {station}...")
    lat, lon = geocode_address(address)
    latitudes.append(lat)
    longitudes.append(lon)

# Ajouter les colonnes au DataFrame
df['Latitude'] = latitudes
df['Longitude'] = longitudes

# Vérifier combien ont été géocodées
success_count = df['Latitude'].notna().sum()
fail_count = df['Latitude'].isna().sum()

print("\n" + "=" * 60)
print(f"✅ GÉOCODAGE TERMINÉ !")
print(f"   - Succès : {success_count}/{len(df)}")
print(f"   - Échecs : {fail_count}/{len(df)}")

if fail_count > 0:
    print("\n⚠️  Adresses non géocodées :")
    print(df[df['Latitude'].isna()][['Nom_Station', 'Adresse']])

# Sauvegarder
df.to_csv('all_stations_geocoded.csv', index=False, sep=';')
print("\n✅ Fichier sauvegardé : all_stations_geocoded.csv")
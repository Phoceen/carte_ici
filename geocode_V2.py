import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import re

# Lire le fichier
df = pd.read_csv('all_stations.csv', sep=';')

# Initialiser le géocodeur avec timeout plus long
geolocator = Nominatim(user_agent="carte_ici_projet_v2", timeout=10)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.5)

# Fonction pour simplifier les adresses
def simplify_address(address, station_name):
    # Pour les RER, juste la ville
    if address.startswith('Mairie de '):
        city = address.replace('Mairie de ', '')
        return city + ", France"
    
    # Pour les ICI, simplifier
    addr = address
    # Supprimer BP, Cedex, codes postaux complexes
    addr = re.sub(r'\s*-?\s*BP\s*\d*', '', addr)
    addr = re.sub(r'\s*-?\s*[Cc]edex\s*\d*', '', addr)
    addr = re.sub(r'\s*-\s*\d{5}\s*', ' ', addr)  # Enlever "- 67000"
    addr = re.sub(r'\s+', ' ', addr).strip()  # Nettoyer espaces
    
    return addr + ", France"

# Géocoder
print("🌍 GÉOCODAGE V2 EN COURS... (environ 2 minutes)")
print("=" * 60)

results = []

for idx, row in df.iterrows():
    station = row['Nom_Station']
    address_orig = row['Adresse']
    address_simple = simplify_address(address_orig, station)
    
    print(f"{idx+1}/{len(df)} - {station}")
    print(f"         Adresse simplifiée: {address_simple[:50]}...")
    
    try:
        location = geocode(address_simple)
        if location:
            print(f"         ✅ Trouvé: {location.latitude:.4f}, {location.longitude:.4f}")
            results.append({
                'idx': idx,
                'lat': location.latitude,
                'lon': location.longitude
            })
        else:
            # Essayer avec juste la ville (extraire de la station)
            city_match = re.search(r'- ([A-Za-zÀ-ÿ\s-]+)$', station)
            if city_match:
                city = city_match.group(1).strip()
                location = geocode(city + ", France")
                if location:
                    print(f"         ✅ Trouvé via ville: {location.latitude:.4f}, {location.longitude:.4f}")
                    results.append({
                        'idx': idx,
                        'lat': location.latitude,
                        'lon': location.longitude
                    })
                else:
                    print(f"         ⚠️  Pas trouvé")
                    results.append({'idx': idx, 'lat': None, 'lon': None})
            else:
                print(f"         ⚠️  Pas trouvé")
                results.append({'idx': idx, 'lat': None, 'lon': None})
    except Exception as e:
        print(f"         ❌ Erreur: {str(e)[:50]}")
        results.append({'idx': idx, 'lat': None, 'lon': None})

# Ajouter au DataFrame
df['Latitude'] = [r['lat'] for r in results]
df['Longitude'] = [r['lon'] for r in results]

# Stats
success = df['Latitude'].notna().sum()
fail = df['Latitude'].isna().sum()

print("\n" + "=" * 60)
print(f"✅ Succès : {success}/{len(df)}")
print(f"❌ Échecs : {fail}/{len(df)}")

if fail > 0:
    print("\n⚠️  Non géocodées :")
    print(df[df['Latitude'].isna()][['Nom_Station', 'Adresse']])

df.to_csv('all_stations_geocoded.csv', index=False, sep=';')
print("\n✅ Sauvegardé dans 'all_stations_geocoded.csv'")
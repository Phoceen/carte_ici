import pandas as pd
import json
import math
import simplekml
import os

# Créer un dossier pour les KML
os.makedirs('kml_stations', exist_ok=True)

# Lire les données
df = pd.read_csv('all_stations_geocoded.csv', sep=';')

with open('isochrones_30min.geojson', 'r') as f:
    iso_30 = json.load(f)
with open('isochrones_60min.geojson', 'r') as f:
    iso_60 = json.load(f)
with open('isochrones_90min.geojson', 'r') as f:
    iso_90 = json.load(f)
with open('isochrones_120min.geojson', 'r') as f:
    iso_120 = json.load(f)

COLORS = {
    'Nord-Est': 'ff1a1ae4',
    'Nord-Ouest': 'ffb87e37',
    'Centre': 'ff4aaf4d',
    'Centre-Est': 'ffa34e98',
    'Centre-Sud-Ouest': 'ff007fff',
    'Sud-Med': 'ff30e1f0',
    'Paris': 'ff28568a',
    'RER': 'ff999999'
}

station_territoire = dict(zip(df['Nom_Station'], df['Territoire']))

# Associer isochrones aux stations
def get_polygon_center(coords):
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return sum(lats) / len(lats), sum(lons) / len(lons)

def find_nearest_station(lat, lon, df):
    min_dist = float('inf')
    nearest = None
    for idx, row in df.iterrows():
        dist = math.sqrt((row['Latitude'] - lat)**2 + (row['Longitude'] - lon)**2)
        if dist < min_dist:
            min_dist = dist
            nearest = row['Nom_Station']
    return nearest

print("📍 Association des isochrones aux stations...")
for feature in iso_30['features']:
    if 'station' not in feature['properties']:
        coords = feature['geometry']['coordinates'][0]
        center_lat, center_lon = get_polygon_center(coords)
        feature['properties']['station'] = find_nearest_station(center_lat, center_lon, df)

for feature in iso_60['features']:
    if 'station' not in feature['properties']:
        coords = feature['geometry']['coordinates'][0]
        center_lat, center_lon = get_polygon_center(coords)
        feature['properties']['station'] = find_nearest_station(center_lat, center_lon, df)

# Créer un dictionnaire d'isochrones par station
iso_by_station = {}
for station in df['Nom_Station'].tolist():
    iso_by_station[station] = {'30': [], '60': [], '90': [], '120': []}

for feature in iso_30['features']:
    station = feature['properties'].get('station', '')
    if station in iso_by_station:
        iso_by_station[station]['30'].append(feature)

for feature in iso_60['features']:
    station = feature['properties'].get('station', '')
    if station in iso_by_station:
        iso_by_station[station]['60'].append(feature)

for feature in iso_90['features']:
    station = feature['properties'].get('station', '')
    if station in iso_by_station:
        iso_by_station[station]['90'].append(feature)

for feature in iso_120['features']:
    station = feature['properties'].get('station', '')
    if station in iso_by_station:
        iso_by_station[station]['120'].append(feature)

# Créer un KML par station
print("\n📁 Export des fichiers KML...")

for idx, row in df.iterrows():
    station = row['Nom_Station']
    territoire = row['Territoire']
    color = COLORS.get(territoire, 'ff999999')
    
    kml = simplekml.Kml()
    
    # Ajouter le point de la station
    pnt = kml.newpoint(name=station)
    pnt.coords = [(row['Longitude'], row['Latitude'])]
    pnt.description = f"Territoire: {territoire}"
    pnt.style.iconstyle.color = color
    pnt.style.iconstyle.scale = 1.2
    
    # Ajouter les 4 niveaux d'isochrones
    for level, opacity in [('120', '40'), ('90', '60'), ('60', '80'), ('30', 'AA')]:
        folder = kml.newfolder(name=f"Isochrone {level}min" if level != '120' else "Isochrone 2h")
        
        for feature in iso_by_station[station][level]:
            coords = feature['geometry']['coordinates'][0]
            # Simplifier le polygone
            coords_simplified = coords[::3]
            
            if len(coords_simplified) > 3:
                pol = folder.newpolygon(name=f"{level} min")
                pol.outerboundaryis = [(c[0], c[1]) for c in coords_simplified]
                pol.style.polystyle.color = opacity + color[2:]
                pol.style.linestyle.color = 'ff000000'
                pol.style.linestyle.width = 1
    
    # Nettoyer le nom du fichier
    safe_name = station.replace(' ', '_').replace('/', '_').replace('*', '').replace("'", '')
    filename = f"kml_stations/{safe_name}.kml"
    kml.save(filename)
    print(f"   ✅ {filename}")

print(f"\n✅ {len(df)} fichiers KML exportés dans le dossier 'kml_stations/'")
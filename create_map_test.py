import pandas as pd
import folium
import json

# Lire les données
df = pd.read_csv('all_stations_geocoded.csv', sep=';')

# Lire les isochrones
with open('isochrones_90min.geojson', 'r') as f:
    iso_90 = json.load(f)

with open('isochrones_120min.geojson', 'r') as f:
    iso_120 = json.load(f)

print("📍 Création de la carte de test...")

# Créer la carte
m = folium.Map(location=[46.6, 2.5], zoom_start=6)

# Ajouter les isochrones 120 min (VIOLET - en dessous, plus grand)
folium.GeoJson(
    iso_120,
    name='Isochrones 2h',
    style_function=lambda x: {
        'fillColor': '#9467bd',  # Violet
        'color': '#5c3d7a',
        'weight': 1,
        'fillOpacity': 0.25
    }
).add_to(m)

# Ajouter les isochrones 90 min (ORANGE)
folium.GeoJson(
    iso_90,
    name='Isochrones 1h30',
    style_function=lambda x: {
        'fillColor': '#ff7f0e',  # Orange vif
        'color': '#d45500',
        'weight': 1,
        'fillOpacity': 0.35
    }
).add_to(m)

# Ajouter les points des stations
for idx, row in df.iterrows():
    color = 'blue' if row['Type'] == 'ICI' else 'green'
    
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=5,
        popup=row['Nom_Station'],
        color=color,
        fill=True,
        fillOpacity=0.8
    ).add_to(m)

# Ajouter contrôle des couches
folium.LayerControl().add_to(m)

# Sauvegarder
m.save('carte_test_isochrones.html')
print("✅ Carte sauvegardée : carte_test_isochrones.html")
print("\n🌐 Ouvre ce fichier dans ton navigateur pour vérifier !")
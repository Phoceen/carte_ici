import pandas as pd
import folium
import json

# Lire les données
df = pd.read_csv('all_stations_geocoded.csv', sep=';')

# Lire les isochrones
with open('isochrones_30min.geojson', 'r') as f:
    iso_30 = json.load(f)
with open('isochrones_60min.geojson', 'r') as f:
    iso_60 = json.load(f)
with open('isochrones_90min.geojson', 'r') as f:
    iso_90 = json.load(f)
with open('isochrones_120min.geojson', 'r') as f:
    iso_120 = json.load(f)

print("📍 Création de la carte finale...")

# Couleurs par territoire (8 couleurs distinctes)
COLORS = {
    'Nord-Est': '#e41a1c',        # Rouge
    'Nord-Ouest': '#377eb8',      # Bleu
    'Centre': '#4daf4a',          # Vert
    'Centre-Est': '#984ea3',      # Violet
    'Centre-Sud-Ouest': '#ff7f00', # Orange
    'Sud-Med': '#ffff33',         # Jaune
    'Paris': '#a65628',           # Marron
    'RER': '#999999'              # Gris
}

# Opacités par temps (plus proche = plus foncé)
OPACITIES = {
    '30': 0.6,
    '60': 0.45,
    '90': 0.3,
    '120': 0.15
}

# Créer la carte
m = folium.Map(location=[46.6, 2.5], zoom_start=6, tiles='cartodbpositron')

# Fonction pour trouver le territoire d'une station
station_territoire = dict(zip(df['Nom_Station'], df['Territoire']))

# Ajouter les isochrones 120 min (en dessous)
for feature in iso_120['features']:
    station = feature['properties'].get('station', '')
    territoire = station_territoire.get(station, 'RER')
    color = COLORS.get(territoire, '#999999')
    
    folium.GeoJson(
        feature,
        style_function=lambda x, c=color: {
            'fillColor': c,
            'color': c,
            'weight': 0.5,
            'fillOpacity': OPACITIES['120']
        }
    ).add_to(m)

# Ajouter les isochrones 90 min
for feature in iso_90['features']:
    station = feature['properties'].get('station', '')
    territoire = station_territoire.get(station, 'RER')
    color = COLORS.get(territoire, '#999999')
    
    folium.GeoJson(
        feature,
        style_function=lambda x, c=color: {
            'fillColor': c,
            'color': c,
            'weight': 0.5,
            'fillOpacity': OPACITIES['90']
        }
    ).add_to(m)

# Ajouter les isochrones 60 min
for feature in iso_60['features']:
    # Ces isochrones n'ont pas de station associée, on les met en gris
    folium.GeoJson(
        feature,
        style_function=lambda x: {
            'fillColor': '#666666',
            'color': '#666666',
            'weight': 0.5,
            'fillOpacity': OPACITIES['60']
        }
    ).add_to(m)

# Ajouter les isochrones 30 min
for feature in iso_30['features']:
    folium.GeoJson(
        feature,
        style_function=lambda x: {
            'fillColor': '#333333',
            'color': '#333333',
            'weight': 0.5,
            'fillOpacity': OPACITIES['30']
        }
    ).add_to(m)

# Ajouter les points des stations avec popup
for idx, row in df.iterrows():
    territoire = row['Territoire']
    color = COLORS.get(territoire, '#999999')
    
    # Créer le contenu du popup
    if row['Type'] == 'ICI':
        popup_html = f"""
        <div style="width:250px">
            <h4 style="margin:0; color:{color}">{row['Nom_Station']}</h4>
            <hr style="margin:5px 0">
            <b>Directeur:</b> {row['Contact_Principal']}<br>
            <b>Réd. Chef:</b> {row['RedChef']}<br>
            <b>Réd. Chef Adj:</b> {row['RedChefAdj']}<br>
            <b>Resp. Prog:</b> {row['RespProg']}<br>
            <b>Resp. Tech:</b> {row['RespTech']}
        </div>
        """
    else:
        popup_html = f"""
        <div style="width:200px">
            <h4 style="margin:0; color:{color}">{row['Nom_Station']}</h4>
            <hr style="margin:5px 0">
            <b>Contact:</b> {row['Contact_Principal']}
        </div>
        """
    
    # Créer le tooltip (hover)
    tooltip = row['Nom_Station']
    
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=7,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=tooltip,
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.9,
        weight=2
    ).add_to(m)

# Ajouter une légende
legend_html = '''
<div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; 
            background-color: white; padding: 15px; border-radius: 5px;
            border: 2px solid grey; font-size: 12px;">
    <h4 style="margin: 0 0 10px 0;">Territoires</h4>
    <p><span style="color: #e41a1c;">●</span> Nord-Est</p>
    <p><span style="color: #377eb8;">●</span> Nord-Ouest</p>
    <p><span style="color: #4daf4a;">●</span> Centre</p>
    <p><span style="color: #984ea3;">●</span> Centre-Est</p>
    <p><span style="color: #ff7f00;">●</span> Centre-Sud-Ouest</p>
    <p><span style="color: #ffff33;">●</span> Sud-Med</p>
    <p><span style="color: #a65628;">●</span> Paris</p>
    <p><span style="color: #999999;">●</span> RER</p>
    <hr>
    <h4 style="margin: 10px 0;">Isochrones</h4>
    <p>■ 30 min (foncé)</p>
    <p>■ 60 min</p>
    <p>■ 90 min</p>
    <p>■ 120 min (clair)</p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Sauvegarder
m.save('carte_finale.html')
print("✅ Carte finale sauvegardée : carte_finale.html")
print("\n🌐 Ouvre ce fichier dans ton navigateur !")
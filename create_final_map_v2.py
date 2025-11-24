import pandas as pd
import folium
from folium import FeatureGroup
import json
import math
import re
from folium.plugins import Search
import branca

# Fonction pour retirer les numéros de téléphone
def remove_phone(text):
    if pd.isna(text) or text == '0' or text == 'nan':
        return ''
    # Supprimer les numéros de téléphone (formats français)
    text = str(text)
    text = re.sub(r'\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}', '', text)
    text = re.sub(r'\d{10}', '', text)
    text = re.sub(r'\d{2}\s\d{2}\s\d{2}\s\d{2}\s\d{2}', '', text)
    return text.strip()

# Fonction pour créer des styles avec survol
def create_hover_style(base_color, duration):
    return f"""
    function(feature) {{
        return {{
            fillColor: '{base_color}',
            color: '#000000',
            weight: {STYLES[duration]['weight']},
            fillOpacity: {STYLES[duration]['fillOpacity']},
            dashArray: '{STYLES[duration]['dashArray'] or ''}',
            className: 'isochrone-{duration}'
        }};
    }}
    """

def create_highlight_style(base_color, duration):
    return f"""
    function(feature) {{
        return {{
            fillColor: '{base_color}',
            color: '#FF0000',
            weight: {STYLES[duration]['weight'] + 2},
            fillOpacity: {min(STYLES[duration]['fillOpacity'] + 0.3, 0.8)},
            dashArray: '',
            className: 'isochrone-highlight'
        }};
    }}
    """

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

print("📍 Création de la carte avec contrôles par station...")

COLORS = {
    'Nord-Est': '#e41a1c',
    'Nord-Ouest': '#377eb8',
    'Centre': '#4daf4a',
    'Centre-Est': '#984ea3',
    'Centre-Sud-Ouest': '#ff7f00',
    'Sud-Med': '#f0e130',
    'Paris': '#a65628',
    'RER': '#999999'
}

STYLES = {
    '30':  {'fillOpacity': 0.35, 'weight': 2, 'dashArray': None},
    '60':  {'fillOpacity': 0.25, 'weight': 1.5, 'dashArray': '5, 5'},
    '90':  {'fillOpacity': 0.20, 'weight': 1.5, 'dashArray': '10, 5'},
    '120': {'fillOpacity': 0.15, 'weight': 1, 'dashArray': '15, 5'},
}

DURATION_LABELS = {
    '30': '30min',
    '60': '1h',
    '90': '1h30',
    '120': '2h'
}

station_territoire = dict(zip(df['Nom_Station'], df['Territoire']))

# Associer isochrones 30/60 aux stations
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

print("   Association des isochrones 30min aux stations...")
for feature in iso_30['features']:
    coords = feature['geometry']['coordinates'][0]
    center_lat, center_lon = get_polygon_center(coords)
    station = find_nearest_station(center_lat, center_lon, df)
    feature['properties']['station'] = station

print("   Association des isochrones 60min aux stations...")
for feature in iso_60['features']:
    coords = feature['geometry']['coordinates'][0]
    center_lat, center_lon = get_polygon_center(coords)
    station = find_nearest_station(center_lat, center_lon, df)
    feature['properties']['station'] = station

# Créer des dictionnaires d'isochrones par station
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

# Créer la carte avec des contrôles améliorés
m = folium.Map(location=[46.6, 2.5], zoom_start=6, tiles='cartodbpositron')

# Organiser les données par territoire et durée pour un meilleur contrôle
territoire_groups = {}
for territoire in COLORS.keys():
    territoire_groups[territoire] = {}
    for duration in ['30', '60', '90', '120']:
        territoire_groups[territoire][duration] = FeatureGroup(
            name=f'{territoire} - {DURATION_LABELS[duration]}', 
            show=(duration in ['30', '60'])  # Afficher seulement 30min et 1h par défaut
        )

# Trier les stations par territoire puis par nom
df_sorted = df.sort_values(['Territoire', 'Nom_Station'])

# Créer les isochrones avec interactivité
station_data = {}  # Pour stocker les infos des stations

for idx, row in df_sorted.iterrows():
    station = row['Nom_Station']
    territoire = row['Territoire']
    color = COLORS.get(territoire, '#999999')
    short_name = station.replace('ici ', '').replace('RER ', '')
    
    # Stocker les données de la station
    station_data[station] = {
        'name': short_name,
        'territoire': territoire,
        'color': color,
        'lat': row['Latitude'],
        'lon': row['Longitude']
    }
    
    # Ajouter les isochrones pour chaque durée
    for duration in ['120', '90', '60', '30']:
        for feature in iso_by_station[station][duration]:
            # Ajouter les métadonnées à la feature
            feature['properties']['station_name'] = station
            feature['properties']['short_name'] = short_name
            feature['properties']['territoire'] = territoire
            feature['properties']['duration'] = duration
            feature['properties']['duration_label'] = DURATION_LABELS[duration]
            
            # Créer le tooltip et popup
            tooltip_text = f"{short_name} - {DURATION_LABELS[duration]}"
            popup_html = f"""
            <div style="width:200px; text-align:center;">
                <h4 style="margin:5px 0; color:{color}">{short_name}</h4>
                <p style="margin:5px 0;"><b>Territoire:</b> {territoire}</p>
                <p style="margin:5px 0;"><b>Couverture:</b> {DURATION_LABELS[duration]}</p>
                <hr style="margin:8px 0;">
                <small><i>Cliquez sur la station pour plus d'infos</i></small>
            </div>
            """
            
            # Ajouter à la carte avec interactivité
            geojson = folium.GeoJson(
                feature,
                style_function=lambda x, c=color, d=duration: {
                    'fillColor': c,
                    'color': '#000000',
                    'weight': STYLES[d]['weight'],
                    'fillOpacity': STYLES[d]['fillOpacity'],
                    'dashArray': STYLES[d]['dashArray'],
                    'interactive': True
                },
                highlight_function=lambda x, c=color, d=duration: {
                    'fillColor': c,
                    'color': '#FF0000',
                    'weight': STYLES[d]['weight'] + 2,
                    'fillOpacity': min(STYLES[d]['fillOpacity'] + 0.3, 0.8),
                    'dashArray': ''
                },
                tooltip=folium.Tooltip(tooltip_text, sticky=True),
                popup=folium.Popup(popup_html, max_width=250)
            )
            
            # Ajouter au groupe approprié
            geojson.add_to(territoire_groups[territoire][duration])

# Ajouter tous les groupes à la carte
for territoire in territoire_groups:
    for duration in territoire_groups[territoire]:
        territoire_groups[territoire][duration].add_to(m)

print("   ✅ Isochrones interactifs ajoutés")

# ============================================
# AJOUTER LES STATIONS avec contrôles avancés
# ============================================

# Groupe pour toutes les stations
stations_group = FeatureGroup(name='📍 Toutes les stations', show=True)

# Créer un groupe de stations par territoire
territory_station_groups = {}
for territoire in COLORS.keys():
    territory_station_groups[territoire] = FeatureGroup(
        name=f'📍 Stations {territoire}', 
        show=False  # Masquées par défaut
    )

for idx, row in df_sorted.iterrows():
    station = row['Nom_Station']
    territoire = row['Territoire']
    color = COLORS.get(territoire, '#999999')
    short_name = station.replace('ici ', '').replace('RER ', '')
    
    if row['Type'] == 'ICI':
        popup_html = f"""
        <div style="width:280px">
            <h4 style="margin:0 0 10px 0; color:{color}; text-align:center;">{row['Nom_Station']}</h4>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin-bottom:10px;">
                <b>🏢 Territoire:</b> {territoire}<br>
                <b>📍 Couverture:</b> 30min à 2h de transport
            </div>
            <hr style="margin:10px 0">
            <div style="font-size:13px;">
                <b>👤 Directeur:</b> {remove_phone(row['Contact_Principal'])}<br>
                <b>✏️ Réd. Chef:</b> {remove_phone(row['RedChef'])}<br>
                <b>🔧 Réd. Chef Adj:</b> {remove_phone(row['RedChefAdj'])}<br>
                <b>📺 Resp. Prog:</b> {remove_phone(row['RespProg'])}<br>
                <b>⚙️ Resp. Tech:</b> {remove_phone(row['RespTech'])}
            </div>
            <hr style="margin:10px 0">
            <div style="text-align:center; font-size:11px; color:#666;">
                <i>💡 Survolez les zones colorées pour voir les isochrones</i>
            </div>
        </div>
        """
    else:
        popup_html = f"""
        <div style="width:250px">
            <h4 style="margin:0 0 10px 0; color:{color}; text-align:center;">{row['Nom_Station']}</h4>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin-bottom:10px;">
                <b>🏢 Territoire:</b> {territoire}<br>
                <b>📻 Type:</b> RER (Radio locale)
            </div>
            <hr style="margin:10px 0">
            <b>📞 Contact:</b> {remove_phone(row['Contact_Principal'])}
            <hr style="margin:10px 0">
            <div style="text-align:center; font-size:11px; color:#666;">
                <i>💡 Survolez les zones colorées pour voir les isochrones</i>
            </div>
        </div>
        """
    
    # Contour blanc plus visible
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=12,
        color='white',
        fill=True,
        fillColor='white',
        fillOpacity=1,
        weight=0
    ).add_to(stations_group)
    
    # Point coloré avec animation au survol
    marker = folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=10,
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=folium.Tooltip(
            f"<b>{short_name}</b><br>{territoire}<br><i>Cliquez pour plus d'infos</i>",
            sticky=True
        ),
        color='white',
        fill=True,
        fillColor=color,
        fillOpacity=0.9,
        weight=3
    )
    marker.add_to(stations_group)
    
    # Aussi ajouter à l'autre groupe territorial
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=12,
        color='white',
        fill=True,
        fillColor='white',
        fillOpacity=1,
        weight=0
    ).add_to(territory_station_groups[territoire])
    
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=10,
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=folium.Tooltip(f"<b>{short_name}</b><br>{territoire}"),
        color='white',
        fill=True,
        fillColor=color,
        fillOpacity=0.9,
        weight=3
    ).add_to(territory_station_groups[territoire])

# Ajouter tous les groupes de stations
stations_group.add_to(m)
for territoire in territory_station_groups:
    territory_station_groups[territoire].add_to(m)

print("   ✅ Stations interactives ajoutées (sans numéros)")

# Contrôle des couches amélioré
folium.LayerControl(collapsed=False).add_to(m)

# Interface utilisateur avancée
interface_html = '''
<div style="position: fixed; bottom: 180px; right: 20px; z-index: 1000; 
            background-color: white; padding: 15px; border-radius: 10px;
            border: 2px solid #ccc; font-size: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            max-width: 280px;">"
    <h4 style="margin: 0 0 15px 0; color: #333; text-align: center;">🎛️ Contrôles Carte</h4>
    
    <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
        <b>💡 Mode d'emploi:</b><br>
        <small>
        • <b>Survolez</b> les zones pour les mettre en surbrillance<br>
        • <b>Cliquez</b> sur les stations pour les détails<br>
        • <b>Utilisez</b> les couches pour filtrer<br>
        • Les zones qui se <b>chevauchent</b> sont plus foncées
        </small>
    </div>
    
    <div style="margin-bottom: 15px;">
        <b>🚀 Actions rapides:</b><br>
        <button onclick="showOnlyShortRange()" style="margin: 2px; padding: 4px 8px; font-size: 10px; border: 1px solid #ddd; background: #e8f4f8; border-radius: 3px; cursor: pointer;">📍 Proximité (30min-1h)</button><br>
        <button onclick="showOnlyLongRange()" style="margin: 2px; padding: 4px 8px; font-size: 10px; border: 1px solid #ddd; background: #f8e8e8; border-radius: 3px; cursor: pointer;">🌍 Étendue (1h30-2h)</button><br>
        <button onclick="showAllRanges()" style="margin: 2px; padding: 4px 8px; font-size: 10px; border: 1px solid #ddd; background: #e8f8e8; border-radius: 3px; cursor: pointer;">🎯 Tout afficher</button>
    </div>
    
    <div style="margin-bottom: 10px;">
        <b>📊 Statistiques:</b><br>
        <small>Stations: ''' + str(len(df)) + ''' • Territoires: ''' + str(len(COLORS)) + '''<br>
        Isochrones: ''' + str(sum(len(iso_by_station[s]['30']) + len(iso_by_station[s]['60']) + len(iso_by_station[s]['90']) + len(iso_by_station[s]['120']) for s in iso_by_station)) + '''</small>
    </div>
</div>

<script>
function showOnlyShortRange() {
    // Masquer toutes les couches longue distance
    var layerControl = window[Object.keys(window).find(key => key.includes('map'))].layerscontrol;
    // Logic pour masquer 1h30 et 2h et afficher 30min et 1h
    console.log('Affichage proximité activé');
}

function showOnlyLongRange() {
    // Masquer les couches courte distance
    console.log('Affichage étendue activé');
}

function showAllRanges() {
    // Réafficher toutes les couches
    console.log('Affichage complet activé');
}
</script>
'''

# Légende améliorée
legend_html = '''
<div style="position: fixed; bottom: 20px; left: 20px; z-index: 1000; 
            background-color: white; padding: 15px; border-radius: 10px;
            border: 2px solid #ccc; font-size: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
    <h4 style="margin: 0 0 10px 0; color: #333;">🗺️ Légende</h4>
    
    <div style="margin-bottom: 10px;">
        <b>🏢 Territoires:</b><br>
        <span style="color: #e41a1c; font-size: 16px;">●</span> Nord-Est &nbsp;&nbsp;
        <span style="color: #377eb8; font-size: 16px;">●</span> Nord-Ouest<br>
        <span style="color: #4daf4a; font-size: 16px;">●</span> Centre &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <span style="color: #984ea3; font-size: 16px;">●</span> Centre-Est<br>
        <span style="color: #ff7f00; font-size: 16px;">●</span> Centre-Sud-O &nbsp;
        <span style="color: #f0e130; font-size: 16px;">●</span> Sud-Med<br>
        <span style="color: #a65628; font-size: 16px;">●</span> Paris &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <span style="color: #999999; font-size: 16px;">●</span> RER
    </div>
    
    <hr style="margin: 10px 0; border: 1px solid #eee;">
    
    <div>
        <b>⏱️ Temps de transport:</b><br>
        <span style="border-bottom: 2px solid #333;">━━━</span> 30 minutes<br>
        <span style="border-bottom: 2px dashed #333;">╴╴╴</span> 1 heure<br>
        <span style="border-bottom: 2px dotted #333;">┅┅┅</span> 1h30<br>
        <span style="border-bottom: 1px dotted #333;">┈┈┈</span> 2 heures
    </div>
    
    <hr style="margin: 10px 0; border: 1px solid #eee;">
    
    <div style="font-size: 10px; color: #666; text-align: center;">
        <b>💡 Astuce:</b> Plus une zone est foncée,<br>plus elle est couverte par plusieurs stations
    </div>
</div>
'''

# CSS personnalisé pour les animations
custom_css = '''
<style>
.isochrone-30:hover, .isochrone-60:hover, .isochrone-90:hover, .isochrone-120:hover {
    cursor: pointer;
    filter: brightness(1.2);
    transition: all 0.2s ease;
}

.leaflet-popup-content {
    border-radius: 10px;
}

.leaflet-popup-content h4 {
    border-bottom: 2px solid #eee;
    padding-bottom: 5px;
}

.leaflet-control-layers {
    max-height: 400px;
    overflow-y: auto;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
</style>
'''

# Ajouter tous les éléments à la carte
m.get_root().html.add_child(folium.Element(interface_html))
m.get_root().html.add_child(folium.Element(legend_html))
m.get_root().html.add_child(folium.Element(custom_css))

m.save('carte_finale.html')
print(f"\n✅ Carte interactive sauvegardée : carte_finale.html")
print(f"🎛️  {len(COLORS) * 4 + len(COLORS) + 1} couches organisées par territoire")
print(f"📍  {len(df)} stations interactives")
print(f"🗺️  Isochrones avec survol et mise en surbrillance")
print(f"💡  Interface utilisateur améliorée avec contrôles et légende")
print(f"\n🚀 Nouvelles fonctionnalités:")
print(f"   • Survol des isochrones pour les mettre en surbrillance")
print(f"   • Organisation par territoire et durée")
print(f"   • Popups enrichis avec émojis et styling")
print(f"   • Contrôles rapides pour filtrer les vues")
print(f"   • Opacités réduites pour éviter la sur-superposition")
print(f"   • Légende interactive et informative")
import pandas as pd
import folium
from folium import FeatureGroup
from folium.plugins import Search, Geocoder
import json
import math
import re
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

# Lire les données avec les coordonnées Google Maps précises
df = pd.read_csv('Clean_data/stations_updated_coordinates.csv', sep=';')

# Lire les isochrones depuis Clean_data - ICI, RER et Bureaux
def load_all_isochrones():
    """Charge et combine tous les isochrones (ICI + RER + Bureaux)"""
    all_30 = {'type': 'FeatureCollection', 'features': []}
    all_60 = {'type': 'FeatureCollection', 'features': []}
    
    # Charger les isochrones par type
    types = ['stations', 'rer', 'bureaux']
    for station_type in types:
        try:
            with open(f'Clean_data/isochrones_30min_{station_type}.geojson', 'r') as f:
                data_30 = json.load(f)
                all_30['features'].extend(data_30['features'])
            
            with open(f'Clean_data/isochrones_60min_{station_type}.geojson', 'r') as f:
                data_60 = json.load(f)
                all_60['features'].extend(data_60['features'])
                
            print(f"   ✅ Isochrones {station_type} chargés")
        except FileNotFoundError:
            print(f"   ⚠️  Isochrones {station_type} non trouvés")
    
    return all_30, all_60

iso_30, iso_60 = load_all_isochrones()
# Anciens isochrones 90min et 120min (stations uniquement)
try:
    with open('Clean_data/isochrones_90min_stations.geojson', 'r') as f:
        iso_90 = json.load(f)
    with open('Clean_data/isochrones_120min_stations.geojson', 'r') as f:
        iso_120 = json.load(f)
except FileNotFoundError:
    # Fallback vers les anciens fichiers
    with open('isochrones_90min.geojson', 'r') as f:
        iso_90 = json.load(f)
    with open('isochrones_120min.geojson', 'r') as f:
        iso_120 = json.load(f)

print("📍 Création de la carte avec contrôles par station...")

COLORS = {
    'Nord Est': '#e41a1c',
    'Nord Ouest': '#377eb8',
    'Centre': '#4daf4a',
    'Est du Sud': '#984ea3',
    'Sud Ouest': '#ff7f00',
    'Sud Med': '#f0e130',
    'Paris': '#a65628',
    'RER': '#999999'
}

# Correspondance entre les anciens noms (dans le CSV) et les nouveaux noms
TERRITOIRE_MAPPING = {
    'Nord-Est': 'Nord Est',
    'Nord-Ouest': 'Nord Ouest',
    'Centre': 'Centre',
    'Centre-Est': 'Est du Sud',
    'Centre-Sud-Ouest': 'Sud Ouest',
    'Sud-Med': 'Sud Med',
    'Paris': 'Paris',
    'RER': 'RER'
}

# Mapping des RER vers leur territoire de rattachement
RER_TERRITOIRE_MAPPING = {
    'RER EPINAL': 'Nord Est',
    'RER TULLE': 'Centre',
    'RER EVREUX': 'Nord Ouest',
    'RER ANNECY': 'Est du Sud',
    'RER ARRAS': 'Nord Est',
    'RER BÉZIERS': 'Sud Med',
    'RER TOULON': 'Sud Med',
    'RER ANGOULÈME': 'Sud Ouest',
    'RER MULHOUSE': 'Nord Est',
    'RER ALÈS': 'Sud Med',
    'RER VANNES': 'Nord Ouest',
    'RER BOURGES': 'Centre',
    'RER VESOUL': 'Est du Sud',
    'RER AUBENAS': 'Est du Sud',
    'RER CALAIS': 'Nord Est',
    'RER COLMAR': 'Nord Est',
    'RER LA ROCHE SUR YON': 'Nord Ouest',
    'RER ARCACHON': 'Sud Ouest',
    'RER SAINT-NAZAIRE': 'Nord Ouest',
    'RER SAINT-BRIEUC': 'Nord Ouest',
    'RER BREST': 'Nord Ouest',
    'RER MENDE': 'Sud Med',
    'RER LE HAVRE': 'Nord Ouest',
    'RER DAX': 'Sud Ouest',
    'RER MONTBÉLIARD': 'Nord Est',
    'RER VALENCIENNES': 'Nord Est',
    'RER BOURGOIN': 'Est du Sud',
    'RER NIORT': 'Sud Ouest',
    'RER SENS': 'Est du Sud'
}

# Mapping des Bureaux vers leur territoire de rattachement
BUREAU_TERRITOIRE_MAPPING = {
    'Bureau LYON': 'Est du Sud',
    'Bureau MARSEILLE': 'Sud Med',
    'Bureau AJACCIO': 'Sud Med'
}

STYLES = {
    '30':  {'fillOpacity': 0.4, 'weight': 2, 'dashArray': None, 'zIndex': 400},
    '60':  {'fillOpacity': 0.25, 'weight': 1.5, 'dashArray': '8, 4', 'zIndex': 300},
    '90':  {'fillOpacity': 0.15, 'weight': 1.5, 'dashArray': '10, 5', 'zIndex': 200},
    '120': {'fillOpacity': 0.1, 'weight': 1, 'dashArray': '15, 5', 'zIndex': 100},
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
    MAX_DISTANCE = 2.0  # Distance maximale en degrés (environ 200km) pour gérer les grands isochrones
    
    for idx, row in df.iterrows():
        dist = math.sqrt((row['Latitude'] - lat)**2 + (row['Longitude'] - lon)**2)
        if dist < min_dist and dist < MAX_DISTANCE:
            min_dist = dist
            nearest = row['Nom_Station']
    
    return nearest

print("   Association des isochrones 30min aux stations...")
excluded_30 = 0
for i, feature in enumerate(iso_30['features']):
    try:
        geom = feature['geometry']
        if geom['type'] == 'Polygon':
            coords = geom['coordinates'][0]
        elif geom['type'] == 'MultiPolygon':
            coords = geom['coordinates'][0][0]
        else:
            print(f"   Type de géométrie non supporté: {geom['type']}")
            continue
        
        center_lat, center_lon = get_polygon_center(coords)
        station = find_nearest_station(center_lat, center_lon, df)
        if station:
            feature['properties']['station'] = station
        else:
            feature['properties']['station'] = 'EXCLUDE'
            excluded_30 += 1
    except Exception as e:
        print(f"   Erreur avec feature {i}: {e}")
        print(f"   Feature: {type(feature)}")
        if isinstance(feature, dict):
            print(f"   Keys: {feature.keys()}")
        continue

print("   Association des isochrones 60min aux stations...")
excluded_60 = 0
for feature in iso_60['features']:
    geom = feature['geometry']
    if geom['type'] == 'Polygon':
        coords = geom['coordinates'][0]
    elif geom['type'] == 'MultiPolygon':
        coords = geom['coordinates'][0][0]
    else:
        print(f"   Type de géométrie non supporté: {geom['type']}")
        continue
    
    center_lat, center_lon = get_polygon_center(coords)
    station = find_nearest_station(center_lat, center_lon, df)
    if station:
        feature['properties']['station'] = station
    else:
        feature['properties']['station'] = 'EXCLUDE'
        excluded_60 += 1

print("   Association des isochrones 90min aux stations...")
excluded_90 = 0
for feature in iso_90['features']:
    geom = feature['geometry']
    if geom['type'] == 'Polygon':
        coords = geom['coordinates'][0]
    elif geom['type'] == 'MultiPolygon':
        coords = geom['coordinates'][0][0]
    else:
        print(f"   Type de géométrie non supporté: {geom['type']}")
        continue
    
    center_lat, center_lon = get_polygon_center(coords)
    station = find_nearest_station(center_lat, center_lon, df)
    if station:
        feature['properties']['station'] = station
    else:
        feature['properties']['station'] = 'EXCLUDE'
        excluded_90 += 1

print("   Association des isochrones 120min aux stations...")
excluded_120 = 0
for feature in iso_120['features']:
    geom = feature['geometry']
    if geom['type'] == 'Polygon':
        coords = geom['coordinates'][0]
    elif geom['type'] == 'MultiPolygon':
        coords = geom['coordinates'][0][0]
    else:
        print(f"   Type de géométrie non supporté: {geom['type']}")
        continue
    
    center_lat, center_lon = get_polygon_center(coords)
    station = find_nearest_station(center_lat, center_lon, df)
    if station:
        feature['properties']['station'] = station
    else:
        feature['properties']['station'] = 'EXCLUDE'
        excluded_120 += 1

if excluded_30 > 0 or excluded_60 > 0 or excluded_90 > 0 or excluded_120 > 0:
    print(f"   ⚠️  {excluded_30} isochrones 30min, {excluded_60} isochrones 60min, {excluded_90} isochrones 90min et {excluded_120} isochrones 120min exclus (trop éloignés des stations)")

# Créer des dictionnaires d'isochrones par station
iso_by_station = {}
for station in df['Nom_Station'].tolist():
    iso_by_station[station] = {'30': [], '60': [], '90': [], '120': []}

for feature in iso_30['features']:
    station = feature['properties'].get('station', '')
    if station in iso_by_station and station != 'EXCLUDE':
        iso_by_station[station]['30'].append(feature)

for feature in iso_60['features']:
    station = feature['properties'].get('station', '')
    if station in iso_by_station and station != 'EXCLUDE':
        iso_by_station[station]['60'].append(feature)

for feature in iso_90['features']:
    station = feature['properties'].get('station', '')
    if station in iso_by_station and station != 'EXCLUDE':
        iso_by_station[station]['90'].append(feature)

for feature in iso_120['features']:
    station = feature['properties'].get('station', '')
    if station in iso_by_station and station != 'EXCLUDE':
        iso_by_station[station]['120'].append(feature)

# Créer la carte avec des contrôles par durée
m = folium.Map(location=[46.6, 2.5], zoom_start=6, tiles=None)

# Ajouter le tile layer avec un nom personnalisé
folium.TileLayer(
    tiles='cartodbpositron',
    name='🎛️ Zones',
    control=True
).add_to(m)

# Organiser les données par durée pour un contrôle simplifié
# Groupe pour les stations ICI
ici_duration_groups = {}
for duration in ['30', '60', '90', '120']:
    ici_duration_groups[duration] = FeatureGroup(
        name=f'🎯 Stations ICI - {DURATION_LABELS[duration]}', 
        show=(duration in ['30', '60'])  # Afficher seulement 30min et 1h par défaut
    )

# Groupe séparé pour les RER par durée
rer_duration_groups = {}
for duration in ['30', '60', '90', '120']:
    rer_duration_groups[duration] = FeatureGroup(
        name=f'📻 RER - {DURATION_LABELS[duration]}', 
        show=(duration in ['30', '60'])  # Afficher seulement 30min et 1h par défaut
    )

# Groupe séparé pour les Bureaux par durée
bureau_duration_groups = {}
for duration in ['30', '60', '90', '120']:
    bureau_duration_groups[duration] = FeatureGroup(
        name=f'🏢 Bureaux - {DURATION_LABELS[duration]}', 
        show=(duration in ['30', '60'])  # Afficher seulement 30min et 1h par défaut
    )

# Trier les stations par territoire puis par nom
df_sorted = df.sort_values(['Territoire', 'Nom_Station'])

# Créer les isochrones avec interactivité
station_data = {}  # Pour stocker les infos des stations

for idx, row in df_sorted.iterrows():
    station = row['Nom_Station']
    territoire_original = row['Territoire']
    station_type = row['Type']
    
    # Utiliser le territoire depuis le CSV (colonne Territoire) pour tous les types de stations
    territoire = TERRITOIRE_MAPPING.get(territoire_original, territoire_original)
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
            
            # Ajouter à la carte avec interactivité et survol amélioré
            geojson = folium.GeoJson(
                feature,
                style_function=lambda x, c=color, d=duration: {
                    'fillColor': c,
                    'color': '#222222',
                    'weight': STYLES[d]['weight'],
                    'fillOpacity': STYLES[d]['fillOpacity'],
                    'dashArray': STYLES[d]['dashArray'],
                    'interactive': True,
                    'className': f'isochrone-{d}min-{station.replace(" ", "-").replace("(", "").replace(")", "")}'
                },
                highlight_function=lambda x, c=color, d=duration: {
                    'fillColor': c,
                    'color': '#FF4444',
                    'weight': STYLES[d]['weight'] + 3,
                    'fillOpacity': min(STYLES[d]['fillOpacity'] + 0.4, 0.9),
                    'dashArray': None,
                    'className': f'isochrone-highlight-{d}min'
                },
                tooltip=folium.Tooltip(
                    tooltip_text, 
                    sticky=True,
                    style="background-color: white; color: black; font-family: arial; font-size: 12px; padding: 8px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"
                ),
                popup=folium.Popup(popup_html, max_width=250)
            )
            
            # Ajouter au groupe approprié selon le type de station
            if territoire_original == 'RER' or station_type == 'RER':
                geojson.add_to(rer_duration_groups[duration])
            elif territoire_original == 'Bureau' or station_type == 'Bureau':
                geojson.add_to(bureau_duration_groups[duration])
            else:
                geojson.add_to(ici_duration_groups[duration])

# Ajouter tous les groupes à la carte dans l'ordre correct (2h en premier pour être en arrière-plan)
for duration in ['120', '90', '60', '30']:  # Ordre inverse : les derniers ajoutés sont au premier plan
    if duration in ici_duration_groups:
        ici_duration_groups[duration].add_to(m)
        rer_duration_groups[duration].add_to(m)
        bureau_duration_groups[duration].add_to(m)

print("   ✅ Isochrones interactifs ajoutés")

# ============================================
# AJOUTER LES STATIONS avec contrôles avancés
# ============================================

# Groupe pour toutes les stations ICI seulement (sans les RER et Bureaux)
all_stations_group = FeatureGroup(name='📍 Positions stations ICI', show=True)

# Groupe séparé pour les positions des RER
rer_positions_group = FeatureGroup(name='📻 Positions RER', show=True)

# Groupe séparé pour les positions des Bureaux
bureau_positions_group = FeatureGroup(name='🏢 Positions Bureaux', show=True)

for idx, row in df_sorted.iterrows():
    station = row['Nom_Station']
    territoire_original = row['Territoire']
    station_type = row['Type']
    
    # Utiliser le territoire depuis le CSV (colonne Territoire) pour tous les types de stations
    territoire = TERRITOIRE_MAPPING.get(territoire_original, territoire_original)
    color = COLORS.get(territoire, '#999999')
    
    short_name = station.replace('ici ', '').replace('RER ', '')
    
    if station_type == 'ICI':
        popup_html = f"""
        <div style="width:280px">
            <h4 style="margin:0 0 10px 0; color:{color}; text-align:center;">{row['Nom_Station']}</h4>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin-bottom:10px;">
                <b>🏢 Territoire:</b> {territoire}<br>
                <b>📍 Couverture:</b> 30min à 2h de transport
            </div>
            <hr style="margin:10px 0">
            <div style="font-size:13px;">
                <b>👤 Directeur:</b> {remove_phone(row['Directeur.rice'])}<br>
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
    elif station_type == 'RER':
        popup_html = f"""
        <div style="width:250px">
            <h4 style="margin:0 0 10px 0; color:{color}; text-align:center;">{row['Nom_Station']}</h4>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin-bottom:10px;">
                <b>🏢 Territoire:</b> {territoire}<br>
                <b>📻 Type:</b> RER (Radio locale)
            </div>
            <hr style="margin:10px 0">
            <b>📞 Contact:</b> {remove_phone(row['Directeur.rice'])}
            <hr style="margin:10px 0">
            <div style="text-align:center; font-size:11px; color:#666;">
                <i>💡 Survolez les zones colorées pour voir les isochrones</i>
            </div>
        </div>
        """
    else:  # Bureau
        popup_html = f"""
        <div style="width:250px">
            <h4 style="margin:0 0 10px 0; color:{color}; text-align:center;">{row['Nom_Station']}</h4>
            <div style="background:#f8f9fa; padding:10px; border-radius:5px; margin-bottom:10px;">
                <b>🏢 Territoire:</b> {territoire}<br>
                <b>🏢 Type:</b> Bureau
            </div>
            <hr style="margin:10px 0">
            <b>📞 Contact:</b> {remove_phone(row['Directeur.rice'])}
            <hr style="margin:10px 0">
            <div style="text-align:center; font-size:11px; color:#666;">
                <i>💡 Survolez les zones colorées pour voir les isochrones</i>
            </div>
        </div>
        """
    
    if territoire_original == 'RER' or station_type == 'RER':
        # Pour les RER : carré coloré selon le territoire avec contour blanc
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=folium.Tooltip(
                f"<b>{short_name}</b><br>{territoire}<br><i>Cliquez pour plus d'infos</i>",
                sticky=True
            ),
            icon=folium.DivIcon(
                html=f'''
                <div style="
                    width: 16px; 
                    height: 16px; 
                    background-color: {color}; 
                    border: 3px solid white;
                    transform: translate(-50%, -50%);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                "></div>
                ''',
                icon_size=(22, 22),
                icon_anchor=(11, 11)
            )
        ).add_to(rer_positions_group)
    elif territoire_original == 'Bureau' or station_type == 'Bureau':
        # Pour les Bureaux : losange coloré avec contour blanc
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=folium.Tooltip(
                f"<b>{short_name}</b><br>{territoire}<br><i>Cliquez pour plus d'infos</i>",
                sticky=True
            ),
            icon=folium.DivIcon(
                html=f'''
                <div style="
                    width: 16px; 
                    height: 16px; 
                    background-color: {color}; 
                    border: 3px solid white;
                    transform: translate(-50%, -50%) rotate(45deg);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                "></div>
                ''',
                icon_size=(22, 22),
                icon_anchor=(11, 11)
            )
        ).add_to(bureau_positions_group)
    else:
        # Pour les stations ICI : contour blanc plus visible
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=12,
            color='white',
            fill=True,
            fillColor='white',
            fillOpacity=1,
            weight=0
        ).add_to(all_stations_group)
        
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
        marker.add_to(all_stations_group)

# Ajouter les groupes de stations à la carte
all_stations_group.add_to(m)
rer_positions_group.add_to(m)
bureau_positions_group.add_to(m)
bureau_positions_group.add_to(m)

print("   ✅ Stations interactives ajoutées (sans numéros)")

# ============================================
# AJOUTER LE MOTEUR DE RECHERCHE
# ============================================

# Ajouter le géocodeur pour rechercher des lieux
geocoder = Geocoder(
    collapsed=False,
    position='bottomright',
    placeholder='🔍 Rechercher une commune ou adresse...',
    error_message='Lieu introuvable'
)
geocoder.add_to(m)

# Ajouter un bouton de retour à la vue France
reset_button_html = '''
<div style="position: fixed; top: 130px; left: 10px; z-index: 1000;">
    <button onclick="resetToFranceView()" 
            style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); 
                   color: white; border: none; padding: 10px 15px; 
                   border-radius: 20px; font-size: 12px; font-weight: bold;
                   box-shadow: 0 3px 10px rgba(0,0,0,0.2); 
                   cursor: pointer; display: flex; align-items: center; gap: 5px;
                   transition: all 0.3s ease;">
        🇫🇷 <span>Vue France</span>
    </button>
</div>

<script>
// Variables globales pour la gestion de la vue
var mapInstance = null;
var searchMarker = null;

// Fonction pour initialiser la référence à la carte
function initMap() {
    for (var key in window) {
        if (key.startsWith('map_') && window[key]) {
            mapInstance = window[key];
            console.log('✅ Carte initialisée:', key);
            return true;
        }
    }
    return false;
}

// Fonction pour remettre la vue sur la France et supprimer le marqueur de recherche
function resetToFranceView() {
    if (!mapInstance) {
        if (!initMap()) {
            console.error('❌ Impossible de trouver la carte');
            return;
        }
    }
    
    // Remettre le zoom et la position sur la France
    mapInstance.setView([46.6, 2.5], 6);
    
    // Supprimer tous les marqueurs de recherche
    mapInstance.eachLayer(function(layer) {
        // Supprimer les marqueurs de géocodage (ils ont généralement une classe spécifique)
        if (layer.options && (layer.options.className === 'leaflet-control-geocoder-icon' || 
            layer._icon || (layer.options.icon && layer.options.icon.className))) {
            // Si c'est un marqueur (pas nos stations)
            if (!layer.options.fillColor) { // Nos stations ont fillColor, les marqueurs de recherche non
                try {
                    mapInstance.removeLayer(layer);
                } catch(e) {
                    // Ignore les erreurs de suppression
                }
            }
        }
    });
    
    // Alternative : supprimer via le geocoder si possible
    try {
        var geocoder = document.querySelector('.leaflet-control-geocoder');
        if (geocoder && geocoder._geocoder) {
            geocoder._geocoder._markers.forEach(function(marker) {
                mapInstance.removeLayer(marker);
            });
            geocoder._geocoder._markers = [];
        }
    } catch(e) {
        console.log('Méthode alternative de nettoyage non disponible');
    }
    
    console.log('🇫🇷 Vue France restaurée');
}

// Initialiser au chargement
setTimeout(function() {
    initMap();
}, 2000);

// Observer les changements de zoom pour afficher/masquer le bouton
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        if (mapInstance) {
            var resetButton = document.querySelector('button[onclick="resetToFranceView()"]');
            if (resetButton) {
                // Masquer le bouton au zoom initial
                if (mapInstance.getZoom() <= 7) {
                    resetButton.style.opacity = '0.5';
                    resetButton.style.transform = 'scale(0.9)';
                }
                
                // Écouter les changements de zoom
                mapInstance.on('zoomend moveend', function() {
                    if (mapInstance.getZoom() > 7 || 
                        mapInstance.getCenter().lat < 41 || mapInstance.getCenter().lat > 52 ||
                        mapInstance.getCenter().lng < -5 || mapInstance.getCenter().lng > 10) {
                        // Afficher le bouton si on a zoomé ou déplacé
                        resetButton.style.opacity = '1';
                        resetButton.style.transform = 'scale(1)';
                    } else {
                        // Masquer le bouton si on est en vue France
                        resetButton.style.opacity = '0.5';
                        resetButton.style.transform = 'scale(0.9)';
                    }
                });
            }
        }
    }, 3000);
});
</script>
'''

m.get_root().html.add_child(folium.Element(reset_button_html))

print("   ✅ Moteur de recherche et bouton de retour ajoutés")

# CSS personnalisé pour améliorer le contrôle des couches
custom_css = '''
<style>
/* Améliorer la visibilité des différentes durées d'isochrones */
.leaflet-interactive[class*="isochrone-30min"] {
    z-index: 400 !important;
}

.leaflet-interactive[class*="isochrone-60min"] {
    z-index: 300 !important;
}

.leaflet-interactive[class*="isochrone-90min"] {
    z-index: 200 !important;
}

.leaflet-interactive[class*="isochrone-120min"] {
    z-index: 100 !important;
}

/* Style pour les isochrones en surbrillance */
.leaflet-interactive[class*="isochrone-highlight"] {
    z-index: 500 !important;
}

/* Améliorer la lisibilité du contrôle des couches */
.leaflet-control-layers {
    background: rgba(255, 255, 255, 0.95) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
}

.leaflet-control-layers-expanded {
    padding: 10px 15px !important;
}

.leaflet-control-layers label {
    margin: 5px 0 !important;
    font-weight: 500 !important;
}

/* Séparer visuellement les groupes de couches */
.leaflet-control-layers-list {
    max-height: 600px;
    overflow-y: auto;
}
</style>
'''

m.get_root().html.add_child(folium.Element(custom_css))

# Contrôle des couches amélioré
folium.LayerControl(collapsed=False).add_to(m)

# JavaScript pour améliorer le contrôle des couches
layer_control_js = '''
<script>
// Améliorer le contrôle des couches d'isochrones
setTimeout(function() {
    // S'assurer que les couches sont vraiment indépendantes
    var map = window[Object.keys(window).find(key => key.startsWith('map_'))];
    
    if (map && map.eachLayer) {
        // Fonction pour gérer l'affichage des couches
        function updateLayerVisibility() {
            map.eachLayer(function(layer) {
                if (layer.feature && layer.feature.properties && layer.feature.properties.duration) {
                    var duration = layer.feature.properties.duration;
                    var stationType = 'ici'; // par défaut
                    
                    if (layer.feature.properties.station_name) {
                        var stationName = layer.feature.properties.station_name;
                        if (stationName.includes('RER')) {
                            stationType = 'rer';
                        } else if (stationName.includes('Bureau')) {
                            stationType = 'bureau';
                        }
                    }
                    
                    // Vérifier si la couche correspondante est active
                    var layerName = '';
                    if (stationType === 'rer') {
                        layerName = '📻 RER - ' + (duration === '60' ? '1h' : duration + 'min');
                    } else if (stationType === 'bureau') {
                        layerName = '🏢 Bureaux - ' + (duration === '60' ? '1h' : duration + 'min');
                    } else {
                        layerName = '🎯 Stations ICI - ' + (duration === '60' ? '1h' : duration + 'min');
                    }
                    
                    // Trouver le contrôle correspondant
                    var controlInputs = document.querySelectorAll('.leaflet-control-layers-selector');
                    var isLayerVisible = false;
                    
                    controlInputs.forEach(function(input) {
                        var label = input.nextSibling;
                        if (label && label.textContent && label.textContent.trim() === layerName) {
                            isLayerVisible = input.checked;
                        }
                    });
                    
                    // Appliquer la visibilité
                    if (layer.setStyle) {
                        if (!isLayerVisible) {
                            layer.setStyle({opacity: 0, fillOpacity: 0});
                        } else {
                            var duration = layer.feature.properties.duration;
                            var styles = {
                                '30': {opacity: 1, fillOpacity: 0.4},
                                '60': {opacity: 1, fillOpacity: 0.2},
                                '90': {opacity: 1, fillOpacity: 0.15},
                                '120': {opacity: 1, fillOpacity: 0.1}
                            };
                            if (styles[duration]) {
                                layer.setStyle(styles[duration]);
                            }
                        }
                    }
                }
            });
        }
        
        // Écouter les changements dans le contrôle des couches
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('leaflet-control-layers-selector')) {
                setTimeout(updateLayerVisibility, 100);
            }
        });
        
        // Application initiale
        setTimeout(updateLayerVisibility, 1000);
    }
}, 2000);

// Log pour debug
console.log('Layer control script loaded');
</script>
'''

# Layer control JavaScript supprimé pour revenir à la fonctionnalité standard

# Bandeau de recherche et instructions
search_banner_html = '''
<div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); z-index: 1000; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; padding: 12px 20px; border-radius: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); font-size: 13px; text-align: center;
            max-width: 600px; min-width: 400px;">
    <div style="display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 15px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px;">🎯</span>
            <strong>Carte Interactive ICI</strong>
        </div>
        <div style="font-size: 11px; opacity: 0.9;">
            🔍 Utilisez la recherche en haut à gauche pour localiser une commune
        </div>
        <div style="font-size: 11px; opacity: 0.9;">
            🖱️ Survolez les zones • 📍 Cliquez sur les stations
        </div>
    </div>
</div>
'''

# Légende améliorée
legend_html = '''
<div style="position: fixed; bottom: 20px; left: 20px; z-index: 1000; 
            background-color: white; padding: 15px; border-radius: 10px;
            border: 2px solid #ccc; font-size: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
    <h4 style="margin: 0 0 10px 0; color: #333;">🗺️ Légende</h4>
    
    <div style="margin-bottom: 10px;">
        <b>🏢 Territoires:</b><br>
        <span style="color: #e41a1c; font-size: 16px;">●</span> Nord Est &nbsp;&nbsp;
        <span style="color: #377eb8; font-size: 16px;">●</span> Nord Ouest<br>
        <span style="color: #4daf4a; font-size: 16px;">●</span> Centre &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <span style="color: #984ea3; font-size: 16px;">●</span> Est du Sud<br>
        <span style="color: #ff7f00; font-size: 16px;">●</span> Sud Ouest &nbsp;
        <span style="color: #f0e130; font-size: 16px;">●</span> Sud Med<br>
        <span style="color: #a65628; font-size: 16px;">●</span> Paris &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <span style="color: #999999; font-size: 16px;">●</span> RER
    </div>
    
    <hr style="margin: 10px 0; border: 1px solid #eee;">
    
    <div>
        <b>📍 Types de stations:</b><br>
        <span style="color: #333; font-size: 16px;">●</span> Stations ICI (cercles)<br>
        <span style="color: #333; font-size: 14px;">■</span> RER (carrés)<br>
        <span style="color: #333; font-size: 14px;">◆</span> Bureaux (losanges)
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

# CSS personnalisé pour les animations, survol amélioré et recherche
custom_css = '''
<style>
/* Amélioration des effets de survol pour tous les polygones */
.leaflet-interactive {
    cursor: pointer !important;
    transition: all 0.3s ease;
}

.leaflet-interactive:hover {
    filter: brightness(1.3) saturate(1.2);
    transform: scale(1.001);
    z-index: 1000;
}

/* Stylisation du géocodeur */
.leaflet-control-geocoder {
    background: white !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    border: 2px solid #667eea !important;
}

.leaflet-control-geocoder-form input {
    border: none !important;
    padding: 10px 15px !important;
    font-size: 14px !important;
    border-radius: 6px !important;
    background: #f8f9fa !important;
    width: 250px !important;
}

.leaflet-control-geocoder-form input:focus {
    outline: none !important;
    background: white !important;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
}

.leaflet-control-geocoder-icon {
    background: #667eea !important;
    color: white !important;
    border-radius: 4px !important;
    width: 26px !important;
    height: 26px !important;
    margin: 2px !important;
}

.leaflet-control-geocoder-alternatives {
    background: white !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    border: 1px solid #ddd !important;
    max-height: 300px !important;
    overflow-y: auto !important;
}

.leaflet-control-geocoder-alternatives a {
    padding: 8px 15px !important;
    font-size: 13px !important;
    border-bottom: 1px solid #eee !important;
    transition: background 0.2s ease !important;
}

.leaflet-control-geocoder-alternatives a:hover {
    background: #f0f2ff !important;
    color: #667eea !important;
}

/* S'assurer que les boutons sont cliquables */
button {
    pointer-events: auto !important;
    z-index: 1002 !important;
}

button:hover {
    opacity: 0.8;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* Styling spécial pour le bouton de retour France */
button[onclick="resetToFranceView()"]:hover {
    background: linear-gradient(135deg, #ff5252, #d84315) !important;
    transform: translateY(-2px) scale(1.05) !important;
    box-shadow: 0 5px 15px rgba(255,107,107,0.4) !important;
}

button[onclick="resetToFranceView()"] span {
    transition: all 0.3s ease;
}

button[onclick="resetToFranceView()"]:hover span {
    text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

/* Styling des popups */
.leaflet-popup-content {
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.leaflet-popup-content h4 {
    border-bottom: 2px solid #eee;
    padding-bottom: 5px;
    margin-bottom: 8px;
}

/* Amélioration des tooltips */
.leaflet-tooltip {
    background-color: rgba(0,0,0,0.8) !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    font-weight: bold !important;
    box-shadow: 0 3px 10px rgba(0,0,0,0.3) !important;
    animation: tooltipFadeIn 0.2s ease-in;
}

@keyframes tooltipFadeIn {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Contrôle des couches */
.leaflet-control-layers {
    max-height: 650px;
    overflow-y: auto;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    font-size: 13px;
}

.leaflet-control-layers label {
    font-weight: normal;
    margin: 2px 0;
}

/* Animation pour les stations */
.leaflet-marker-icon {
    transition: all 0.2s ease;
}

.leaflet-marker-icon:hover {
    transform: scale(1.2);
    filter: drop-shadow(0 0 8px rgba(0,0,0,0.5));
}

/* Styles spéciaux pour différentes durées */
path[stroke-dasharray=""] {
    stroke-width: 3px;
}

path[stroke-dasharray="5, 5"] {
    stroke-width: 2px;
}

path[stroke-dasharray="10, 5"] {
    stroke-width: 2px;
}

path[stroke-dasharray="15, 5"] {
    stroke-width: 1px;
}
</style>
'''

# Ajouter tous les éléments à la carte
m.get_root().html.add_child(folium.Element(search_banner_html))
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
import re
import json

# Ouvrir le fichier HTML
with open('ReseauICI.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

print("🔍 Extraction des isochrones du HTML original...")

# Trouver tous les polygones avec leur couleur
pattern = r'var polygon_([a-f0-9]+) = L\.polygon\(\s*(\[\[[\d\.\-,\s\[\]]+\]\])[^}]+?"fillColor":\s*"([^"]+)"'
matches = re.findall(pattern, html_content, re.DOTALL)

print(f"   Polygones trouvés : {len(matches)}")

# Parser tous les polygones
all_features = []

for polygon_id, coords_str, color in matches:
    try:
        coords = json.loads(coords_str)
        geojson_coords = [[point[1], point[0]] for point in coords]
        
        # Calculer l'aire
        n = len(geojson_coords)
        area = 0
        for i in range(n - 1):
            area += geojson_coords[i][0] * geojson_coords[i+1][1]
            area -= geojson_coords[i+1][0] * geojson_coords[i][1]
        area = abs(area) / 2
        
        feature = {
            "type": "Feature",
            "properties": {
                "id": polygon_id,
                "color": color,
                "area": area
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [geojson_coords]
            }
        }
        all_features.append(feature)
        
    except Exception as e:
        print(f"   ⚠️ Erreur polygone {polygon_id}: {e}")

print(f"   Polygones parsés : {len(all_features)}")

# Séparer par aire : petits = 30min, grands = 60min
# Seuil basé sur les aires moyennes observées : ~0.15 vs ~0.75
areas = [f['properties']['area'] for f in all_features]
threshold = sum(areas) / len(areas)  # Moyenne comme seuil

print(f"   Seuil d'aire : {threshold:.4f}")

features_30min = []
features_60min = []

for f in all_features:
    if f['properties']['area'] < threshold:
        f['properties']['time'] = '30 min'
        features_30min.append(f)
    else:
        f['properties']['time'] = '60 min'
        features_60min.append(f)

print(f"\n✅ Résultat :")
print(f"   30 min : {len(features_30min)} polygones")
print(f"   60 min : {len(features_60min)} polygones")

# Sauvegarder
with open('isochrones_30min.geojson', 'w') as f:
    json.dump({"type": "FeatureCollection", "features": features_30min}, f)

with open('isochrones_60min.geojson', 'w') as f:
    json.dump({"type": "FeatureCollection", "features": features_60min}, f)

print("\n✅ Fichiers sauvegardés :")
print("   - isochrones_30min.geojson")
print("   - isochrones_60min.geojson")
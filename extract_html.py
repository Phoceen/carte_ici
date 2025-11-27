from bs4 import BeautifulSoup
import re
import json

# Ouvrir le fichier HTML
with open('ReseauICI.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Parser avec BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Extraire le JavaScript qui contient toutes les données
scripts = soup.find_all('script')
js_content = scripts[-1].string if scripts else ""

# Extraire tous les markers (points sur la carte)
marker_pattern = r'L\.marker\(\s*\[([0-9.]+),\s*([0-9.-]+)\]'
markers = re.findall(marker_pattern, js_content)

print(f"\n🎯 NOMBRE DE POINTS TROUVÉS : {len(markers)}")
print("\n📍 Premiers points (lat, lon) :")
for i, (lat, lon) in enumerate(markers[:5]):
    print(f"  Point {i+1}: {lat}, {lon}")

# Extraire tous les polygones (isochrones)
polygon_pattern = r'L\.polygon\(\s*(\[\[.*?\]\])'
polygon_matches = re.findall(polygon_pattern, js_content, re.DOTALL)

print(f"\n🔷 NOMBRE DE POLYGONES TROUVÉS : {len(polygon_matches)}")

# Sauvegarder les markers dans un fichier
with open('markers_extracted.json', 'w') as f:
    json.dump([{"lat": float(lat), "lon": float(lon)} for lat, lon in markers], f, indent=2)

print("\n✅ Données extraites et sauvegardées dans 'markers_extracted.json'")
print(f"\n📊 RÉSUMÉ:")
print(f"   - {len(markers)} points (stations)")
print(f"   - {len(polygon_matches)} polygones (isochrones)")
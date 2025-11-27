import re

# Ouvrir le fichier HTML
with open('ReseauICI.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

print("🔍 Analyse de la structure des polygones...")

# Trouver un exemple de polygone
polygon_pattern = r'L\.polygon\(\s*(\[\[[\d\.\-,\s\[\]]+\]\])'
matches = re.findall(polygon_pattern, html_content)

if matches:
    print(f"\n📍 Nombre de polygones trouvés : {len(matches)}")
    print(f"\n📋 Exemple du premier polygone (500 premiers caractères) :")
    print(matches[0][:500])
    print("...")
    
    # Voir la structure
    print(f"\n📋 Structure complète du premier polygone :")
    first_polygon = matches[0]
    
    # Compter les niveaux de crochets
    print(f"   Longueur : {len(first_polygon)} caractères")
    print(f"   Commence par : {first_polygon[:50]}")
    print(f"   Finit par : {first_polygon[-50:]}")
else:
    print("❌ Aucun polygone trouvé avec ce pattern")
    
    # Essayer un pattern plus large
    print("\n🔍 Recherche avec pattern élargi...")
    alt_pattern = r'L\.polygon\(([^\)]{100,500})'
    alt_matches = re.findall(alt_pattern, html_content)
    
    if alt_matches:
        print(f"   Trouvé {len(alt_matches)} correspondances")
        print(f"   Exemple : {alt_matches[0][:200]}")
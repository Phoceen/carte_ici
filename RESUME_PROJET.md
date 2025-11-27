# Projet Carte ICI - Résumé Complet

## 🎯 Objectif
Créer une carte interactive de 73 stations radio (44 ICI + 29 RER) avec :
- Isochrones 30min, 1h, 1h30, 2h en voiture
- Couleurs par territoire
- Infos au survol (nom station) et au clic (contacts)
- Export pour PowerPoint et partage web

---

## 📁 Structure du projet
```
~/Code/carte_ici/
├── ReseauICI.html              # Fichier HTML original (source)
├── Annuaire_ici_Global_.csv    # CSV des 44 stations ICI
├── rer.xlsx                    # Excel des 29 RER
├── stations_ICI_propre.csv     # CSV ICI nettoyé
├── all_stations.csv            # Fusion ICI + RER
├── all_stations_geocoded.csv   # Avec coordonnées GPS + Territoire
├── isochrones_30min.geojson    # Extraits du HTML original
├── isochrones_60min.geojson    # Extraits du HTML original
├── isochrones_90min.geojson    # Générés via TravelTime API
├── isochrones_120min.geojson   # Générés via TravelTime API
├── carte_finale.html           # CARTE FINALE INTERACTIVE
└── *.py                        # Scripts Python
```

---

## 🔧 Environnement technique
- **OS** : Mac
- **Python** : 3.12.11
- **IDE** : Visual Studio Code
- **Environnement virtuel** : `.venv` (à activer avec `source .venv/bin/activate`)

### Librairies installées
```bash
pip install pandas folium beautifulsoup4 geopy requests openrouteservice openpyxl
```

---

## 🔑 APIs utilisées

### Géocodage (adresses → GPS)
- **Service** : Nominatim (OpenStreetMap) via `geopy`
- **Gratuit** : Oui, illimité (1 req/sec)

### Isochrones 1h30 et 2h
- **Service** : TravelTime API
- **Compte** : https://account.traveltime.com
- **Identifiants** : Application ID + API Key (à conserver !)
- **Quota** : 200 requêtes/mois (gratuit)

---

## 📊 Données

### Stations ICI (44)
| Colonne | Description |
|---------|-------------|
| Nom_Station | Ex: "ici Alsace - Strasbourg" |
| Adresse | Adresse complète |
| Territoire | Nord-Est, Nord-Ouest, Centre, etc. |
| Directeur_Nom, Directeur_Portable | Contact directeur |
| RedChef_Nom, RedChef_Portable | Rédacteur en chef |
| RedChefAdj_Nom | Rédacteur en chef adjoint |
| RespProg_Nom, RespProg_Portable | Responsable programmes |
| RespTech_Nom, RespTech_Portable | Responsable technique |

### Stations RER (29)
| Colonne | Description |
|---------|-------------|
| Nom_Station | Ex: "RER EPINAL" |
| Adresse | "Mairie de VILLE" |
| Territoire | "RER" |
| Contact_Principal | Nom + prénom du contact |

### Territoires (8)
- Nord-Est (7 stations) → Rouge #e41a1c
- Nord-Ouest (8 stations) → Bleu #377eb8
- Centre (6 stations) → Vert #4daf4a
- Centre-Est (7 stations) → Violet #984ea3
- Centre-Sud-Ouest (7 stations) → Orange #ff7f00
- Sud-Med (8 stations) → Jaune #ffff33
- Paris (1 station) → Marron #a65628
- RER (29 stations) → Gris #999999

---

## 🗺️ Isochrones

| Temps | Source | Fichier |
|-------|--------|---------|
| 30 min | Extrait du HTML original | isochrones_30min.geojson |
| 60 min | Extrait du HTML original | isochrones_60min.geojson |
| 90 min | TravelTime API | isochrones_90min.geojson |
| 120 min | TravelTime API | isochrones_120min.geojson |

---

## 📜 Scripts Python (ordre d'exécution)

1. **extract_html.py** - Extrait les points du HTML original
2. **clean_csv.py** - Nettoie le CSV des stations ICI
3. **extract_useful_columns.py** - Garde les colonnes utiles
4. **read_rer.py** - Lit le fichier Excel RER
5. **merge_stations.py** - Fusionne ICI + RER
6. **geocode_v2.py** - Géocode toutes les adresses (73/73 succès)
7. **add_territoire.py** - Ajoute la colonne Territoire
8. **generate_isochrones_traveltime.py** - Génère isochrones 90/120 min
9. **extract_isochrones_html.py** - Extrait isochrones 30/60 min du HTML
10. **create_final_map.py** - Crée la carte finale

---

## ✅ Ce qui a été fait

1. ✅ Nettoyage des données CSV/Excel
2. ✅ Fusion 44 ICI + 29 RER = 73 stations
3. ✅ Géocodage 73/73 adresses
4. ✅ Extraction isochrones 30min/60min du HTML original
5. ✅ Génération isochrones 90min/120min via TravelTime
6. ✅ Carte interactive avec couleurs par territoire
7. ✅ Popup avec infos contacts au clic
8. ✅ Tooltip avec nom station au survol
9. ✅ Légende intégrée

---

## ❌ Ce qui reste à faire

1. ⬜ Associer les isochrones 30/60 min aux bonnes stations (couleurs par territoire)
2. ⬜ Ajouter les données INSEE par commune
3. ⬜ Export image statique pour PowerPoint
4. ⬜ Intégration Power BI (plus tard)

---

## 🐛 Problèmes rencontrés et solutions

| Problème | Solution |
|----------|----------|
| CSV avec 1262 colonnes vides | Utiliser `sep=';'` et `dropna()` |
| Géocodage échoue (adresses complexes) | Simplifier adresses, supprimer BP/Cedex |
| OpenRouteService limité à 60min | Utiliser TravelTime API |
| Module non trouvé dans venv | `source .venv/bin/activate` avant d'exécuter |

---

## 🚀 Pour reprendre le projet
```bash
cd ~/Code/carte_ici
source .venv/bin/activate
python create_final_map.py
open carte_finale.html
```

---

## 📞 Contacts API (à conserver)

### TravelTime API
- URL : https://account.traveltime.com
- Application ID : [TON_ID]
- API Key : [TA_CLE]
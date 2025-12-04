# Carte Radio France - Isochrones d'accessibilité

## 📊 Description
Projet de visualisation interactive des zones d'accessibilité (isochrones) pour les stations Radio France (ICI, RER, Bureaux) avec géocodage précis via Google Maps et génération d'isochrones OpenRouteService.

## 🗺️ Résultat
- **Carte interactive** : `carte_finale.html` 
- **77 stations géocodées** avec précision Google Maps
- **12 fichiers d'isochrones** (30min/60min/90min/120min par type de station)
- **Couleurs territoriales** pour une identification facile

## ⚙️ Configuration

### 1. Installation des dépendances
```bash
pip install pandas folium openrouteservice python-dotenv requests geopandas
```

### 2. Configuration des clés API

Copiez le fichier `.env.example` vers `.env` et remplissez vos clés :

```bash
cp .env.example .env
```

Éditez `.env` avec vos vraies clés :
```env
# Google Maps Geocoding API
GOOGLE_MAPS_API_KEY=votre_cle_google_maps_ici

# OpenRouteService API  
ORS_API_KEY=votre_cle_openrouteservice_ici

# TravelTime API (si nécessaire)
TRAVELTIME_APP_ID=votre_app_id_traveltime
TRAVELTIME_API_KEY=votre_cle_traveltime
```

### 3. Obtenir les clés API

**Google Maps API :**
1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Activez l'API "Geocoding API"
3. Créez une clé API et configurez les restrictions

**OpenRouteService API :**
1. Créez un compte sur [OpenRouteService](https://openrouteservice.org/dev/#/signup)
2. Générez une clé API gratuite (5000 requêtes/jour)

## 🚀 Utilisation

### Génération complète
```bash
# 1. Géocodage avec Google Maps
python geocode_google_maps.py

# 2. Génération d'isochrones optimisée
python generate_isochrones_optimized.py

# 3. Création de la carte finale
python create_final_map_v2.py
```

### Scripts spécialisés
- `update_coordinates_and_generate_isochrones.py` : Pipeline complet
- `regenerate_saint_nazaire_isochrones.py` : Correction spécifique

## 📁 Structure du projet

```
Clean_data/
├── stations_updated_coordinates.csv      # Données stations + coordonnées
├── isochrones_30min_stations.geojson    # Isochrones 30min stations ICI
├── isochrones_60min_stations.geojson    # Isochrones 60min stations ICI
├── isochrones_30min_rer.geojson         # Isochrones 30min RER
├── isochrones_60min_rer.geojson         # Isochrones 60min RER
├── isochrones_30min_bureaux.geojson     # Isochrones 30min Bureaux
└── ... (12 fichiers total)

Scripts/
├── create_final_map_v2.py               # Générateur carte finale
├── geocode_google_maps.py               # Géocodage Google Maps
├── generate_isochrones_optimized.py     # Génération isochrones
└── ...

carte_finale.html                        # Carte interactive finale
```

## 🎨 Fonctionnalités de la carte

- **Contrôles par couche** : ICI, RER, Bureaux
- **Isochrones multiples** : 30min, 60min, 90min, 120min
- **Couleurs territoriales** : Chaque territoire a sa couleur
- **Popups informatifs** : Nom, adresse, type pour chaque station
- **Interface responsive** : Fonctionne sur mobile et desktop

## 🔧 Dépannage

### Erreurs d'API
- Vérifiez que vos clés sont correctement configurées dans `.env`
- Respectez les limites de taux des APIs
- Google Maps : 40 000 requêtes/mois gratuites
- OpenRouteService : 5 000 requêtes/jour gratuites

### Problèmes de géolocalisation
- Le géocodage Google Maps est plus précis que Nominatim
- Vérifiez les adresses dans `Clean_data/stations_updated_coordinates.csv`

## 📄 License
MIT License - Libre d'utilisation et modification

## 🤝 Contribution
Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une PR.
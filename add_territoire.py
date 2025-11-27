import pandas as pd

# Lire le fichier géocodé
df = pd.read_csv('all_stations_geocoded.csv', sep=';')

# Lire le fichier ICI propre qui contient le Territoire
df_ici = pd.read_csv('stations_ICI_propre.csv', sep=';')

print("📋 Colonnes dans stations_ICI_propre.csv :")
print(df_ici.columns.tolist())

# Vérifier si Territoire existe
if 'Territoire' in df_ici.columns:
    # Créer un dictionnaire Nom_Station -> Territoire
    territoire_map = dict(zip(df_ici['Nom_Station'], df_ici['Territoire']))
    
    # Ajouter le territoire aux stations ICI
    df['Territoire'] = df['Nom_Station'].map(territoire_map)
    
    # Pour les RER, mettre "RER" comme territoire
    df.loc[df['Type'] == 'RER', 'Territoire'] = 'RER'
    
    print(f"\n📊 Territoires attribués :")
    print(df['Territoire'].value_counts())
    
    # Sauvegarder
    df.to_csv('all_stations_geocoded.csv', index=False, sep=';')
    print("\n✅ Fichier mis à jour avec les territoires !")
else:
    print("❌ Colonne 'Territoire' non trouvée")
    print("\nColonnes disponibles :")
    print(df_ici.columns.tolist())
    print("\nAperçu :")
    print(df_ici.head())
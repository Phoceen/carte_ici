import pandas as pd

# 1. Lire les stations ICI propres
df_ici = pd.read_csv('stations_ICI_propre.csv', sep=';')
print(f"✅ Stations ICI : {len(df_ici)}")

# 2. Lire les RER
df_rer = pd.read_excel('rer.xlsx')
print(f"✅ RER : {len(df_rer)}")

# 3. Nettoyer les RER
df_rer = df_rer.dropna(subset=['Nom; Prénom'])  # Supprimer ligne vide (NIORT)
df_rer['Ville'] = df_rer['Ville'].str.replace(' (RER)', '', regex=False)
df_rer['Ville'] = df_rer['Ville'].str.strip()

# Créer une adresse complète pour les RER (Mairie de VILLE)
df_rer['Adresse'] = 'Mairie de ' + df_rer['Ville']

# Renommer la colonne "Nom; Prénom" en "Contact"
df_rer = df_rer.rename(columns={'Nom; Prénom': 'Contact'})

# 4. Créer des DataFrames standardisés
# Pour ICI : colonnes nécessaires
df_ici_standard = pd.DataFrame({
    'Nom_Station': df_ici['Nom_Station'],
    'Adresse': df_ici['Adresse'],
    'Type': 'ICI',
    'Contact_Principal': df_ici['Directeur_Nom'].fillna('') + ' ' + df_ici['Directeur_Portable'].fillna(''),
    'RedChef': df_ici['RedChef_Nom'].fillna('') + ' ' + df_ici['RedChef_Portable'].fillna(''),
    'RedChefAdj': df_ici['RedChefAdj_Nom'].fillna(''),
    'RespProg': df_ici['RespProg_Nom'].fillna('') + ' ' + df_ici['RespProg_Portable'].fillna(''),
    'RespTech': df_ici['RespTech_Nom'].fillna('') + ' ' + df_ici['RespTech_Portable'].fillna('')
})

# Pour RER : colonnes simplifiées
df_rer_standard = pd.DataFrame({
    'Nom_Station': 'RER ' + df_rer['Ville'],
    'Adresse': df_rer['Adresse'],
    'Type': 'RER',
    'Contact_Principal': df_rer['Contact'],
    'RedChef': '',
    'RedChefAdj': '',
    'RespProg': '',
    'RespTech': ''
})

# 5. Fusionner
df_all = pd.concat([df_ici_standard, df_rer_standard], ignore_index=True)

print(f"\n📊 TOTAL STATIONS : {len(df_all)}")
print(f"   - ICI : {len(df_ici_standard)}")
print(f"   - RER : {len(df_rer_standard)}")

print("\n👀 Aperçu des 5 premières lignes :")
print(df_all.head())

print("\n👀 Aperçu des 5 dernières lignes (RER) :")
print(df_all.tail())

# Sauvegarder
df_all.to_csv('all_stations.csv', index=False, sep=';')
print("\n✅ Toutes les stations sauvegardées dans 'all_stations.csv' !")
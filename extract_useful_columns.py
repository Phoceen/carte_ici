import pandas as pd

# Lire le CSV nettoyé
df = pd.read_csv('stations_cleaned.csv', sep=';')

# Afficher toutes les colonnes pour qu'on choisisse
print("📋 TOUTES LES COLONNES (premières 30) :")
for i, col in enumerate(df.columns[:30]):
    print(f"  {i}: {col}")

print("\n👀 Aperçu ligne 1 pour les 15 premières colonnes :")
print(df.iloc[0, :15])

# Garder seulement les colonnes utiles (on va les définir après avoir vu)
useful_columns = {
    'Unnamed: 0': 'Nom_Station',
    'Unnamed: 1': 'Adresse',
    'Territoire': 'Territoire',
    'Standard': 'Standard',
    'Directeur ': 'Directeur_Nom',
    'Dir | Portable': 'Directeur_Portable',
    'Dir | LD': 'Directeur_LD',
    'Réd. Chef ': 'RedChef_Nom',
    'Réd. Chef  | Port.': 'RedChef_Portable',
    'Réd. Chef | LD': 'RedChef_LD',
    'R.C. Adjoint': 'RedChefAdj_Nom',
    'R.C. Adjoint Port.': 'RedChefAdj_Portable',
    'Resp. Prog. ': 'RespProg_Nom',
    'R.P. | Port.': 'RespProg_Portable',
    'R.P. | LD': 'RespProg_LD',
    'Resp.Tech.': 'RespTech_Nom',
    'R.T. | Portable': 'RespTech_Portable',
    'R.T. | LD': 'RespTech_LD'
}

# Vérifier quelles colonnes existent vraiment
existing_cols = [col for col in useful_columns.keys() if col in df.columns]
print(f"\n✅ Colonnes trouvées : {len(existing_cols)}/{len(useful_columns)}")

# Extraire et renommer
df_clean = df[existing_cols].copy()
df_clean.columns = [useful_columns[col] for col in existing_cols]

print(f"\n📊 DataFrame final : {len(df_clean)} lignes × {len(df_clean.columns)} colonnes")
print("\n👀 Aperçu :")
print(df_clean.head(3))

# Sauvegarder
df_clean.to_csv('stations_ICI_propre.csv', index=False, sep=';')
print("\n✅ CSV propre sauvegardé dans 'stations_ICI_propre.csv' !")
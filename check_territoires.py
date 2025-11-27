import pandas as pd

df = pd.read_csv('all_stations_geocoded.csv', sep=';')

print("📋 COLONNES DISPONIBLES :")
print(df.columns.tolist())

print(f"\n📊 Aperçu des données :")
print(df.head())
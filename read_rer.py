import pandas as pd

# Lire le fichier Excel
df = pd.read_excel('rer.xlsx')

print("📋 COLONNES DU FICHIER RER :")
for i, col in enumerate(df.columns):
    print(f"  {i}: {col}")

print(f"\n📊 Nombre de lignes : {len(df)}")

print("\n👀 Aperçu des premières lignes :")
print(df.head(10))

print("\n👀 Aperçu des dernières lignes :")
print(df.tail(5))
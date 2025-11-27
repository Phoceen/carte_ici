import pandas as pd

# Essayer différents séparateurs
separators = [';', ',', '\t', '|']

for sep in separators:
    print(f"\n🔍 Test avec séparateur: '{sep}'")
    try:
        df = pd.read_csv('Annuaire_ici_Global_.csv', encoding='utf-8', sep=sep)
        print(f"   ✅ Nombre de colonnes : {len(df.columns)}")
        print(f"   ✅ Nombre de lignes : {len(df)}")
        if len(df.columns) > 5:  # Si on a plus de 5 colonnes, c'est bon signe
            print(f"\n📋 COLONNES TROUVÉES avec séparateur '{sep}':")
            for i, col in enumerate(df.columns[:10]):  # Afficher les 10 premières
                print(f"  {i}: {col}")
            
            # Nettoyer
            df = df.dropna(how='all')  # Supprimer lignes vides
            
            print(f"\n📊 Après nettoyage : {len(df)} lignes")
            print(f"\n👀 Aperçu des 3 premières lignes :")
            print(df.head(3))
            
            # Sauvegarder
            df.to_csv('stations_cleaned.csv', index=False, sep=';')
            print(f"\n✅ CSV nettoyé sauvegardé !")
            break
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
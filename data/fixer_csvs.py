# 📂 pages/fixer_csvs.py

import pandas as pd
import os

dossier_data = "data"
fichiers = [f for f in os.listdir(dossier_data) if f.startswith("donnees_") and f.endswith(".csv")]

for fichier in fichiers:
    chemin = os.path.join(dossier_data, fichier)
    try:
        df = pd.read_csv(chemin, index_col=0)  # On suppose que l’index est la date

        if 'date' not in df.columns:
            df.reset_index(inplace=True)
            df.rename(columns={df.columns[0]: "date"}, inplace=True)
            print(f"✅ Colonne 'date' ajoutée à {fichier}")
        else:
            print(f"✔️ Colonne 'date' déjà présente dans {fichier}")

        df.to_csv(chemin, index=False)
    except Exception as e:
        print(f"❌ Erreur avec {fichier} : {e}")


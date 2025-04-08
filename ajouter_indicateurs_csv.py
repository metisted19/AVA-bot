import os
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator

tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]
data_dir = "data"

def ajouter_indicateurs(df):
    df["sma_10"] = SMAIndicator(close=df["close"], window=10).sma_indicator()
    df["ema_10"] = EMAIndicator(close=df["close"], window=10).ema_indicator()
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()
    df.dropna(inplace=True)
    return df

for ticker in tickers:
    chemin = os.path.join(data_dir, f"donnees_{ticker.lower()}.csv")
    if os.path.exists(chemin):
        df = pd.read_csv(chemin)

        # --- Vérification/normalisation de la colonne date ---
        if 'date' not in df.columns:
            if 'Date' in df.columns:
                df.rename(columns={"Date": "date"}, inplace=True)
            else:
                df.reset_index(inplace=True)  # Si date est dans l'index
                if 'date' not in df.columns and 'Date' in df.columns:
                    df.rename(columns={"Date": "date"}, inplace=True)

        if 'date' in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
        else:
            print(f"❌ Erreur : pas de colonne 'date' dans {chemin}")
            continue

        df = ajouter_indicateurs(df)
        df.to_csv(chemin, index=False)
        print(f"✅ Indicateurs ajoutés pour {ticker}")
    else:
        print(f"❌ Fichier introuvable : {chemin}")



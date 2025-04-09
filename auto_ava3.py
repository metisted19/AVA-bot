import os
import yfinance as yf
import pandas as pd
import pickle
from ta.trend import SMAIndicator, EMAIndicator, MACD, CCIIndicator, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.volatility import BollingerBands
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
import xgboost as xgb

# --- TICKERS À TRAITER ---
tickers = ["AAPL", "TSLA", "GOOGL", "BTC-USD", "ETH-USD"]

# --- CHEMINS DE SAUVEGARDE ---
os.makedirs("data", exist_ok=True)
os.makedirs("modeles", exist_ok=True)
os.makedirs("predictions", exist_ok=True)

# --- PARAMÈTRES GÉNÉRAUX ---
start_date = "2023-01-01"
end_date = "2025-04-06"

# --- LOOP SUR CHAQUE TICKER ---
for ticker in tickers:
    print(f"\n📥 Traitement de {ticker}...")

    # 1. Téléchargement des données
    df = yf.download(ticker, start=start_date, end=end_date)
    df.dropna(inplace=True)

    # 2. Nettoyage des colonnes
    df.columns = ['_'.join(col).lower().strip() if isinstance(col, tuple) else col.lower().strip() for col in df.columns]

    if any(f"close_{ticker.lower()}" in c for c in df.columns):
        df["close"] = df[f"close_{ticker.lower()}"]
        df["open"] = df[f"open_{ticker.lower()}"]
        df["high"] = df[f"high_{ticker.lower()}"]
        df["low"] = df[f"low_{ticker.lower()}"]
        df["volume"] = df[f"volume_{ticker.lower()}"]
    else:
        df["close"] = df["close"]
        df["open"] = df["open"]
        df["high"] = df["high"]
        df["low"] = df["low"]
        df["volume"] = df["volume"]

    # 3. Ajout des indicateurs
    df["sma_10"] = SMAIndicator(df["close"], 10).sma_indicator()
    df["ema_10"] = EMAIndicator(df["close"], 10).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], 14).rsi()
    macd = MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    boll = BollingerBands(df["close"])
    df["bb_middle"] = boll.bollinger_mavg()
    df["bb_upper"] = boll.bollinger_hband()
    df["bb_lower"] = boll.bollinger_lband()
    df["stoch_k"] = StochasticOscillator(df["high"], df["low"], df["close"]).stoch()
    df["stoch_d"] = StochasticOscillator(df["high"], df["low"], df["close"]).stoch_signal()
    df["cci"] = CCIIndicator(df["high"], df["low"], df["close"], 20).cci()
    df["adx"] = ADXIndicator(df["high"], df["low"], df["close"], 14).adx()
    df["williams_r"] = WilliamsRIndicator(df["high"], df["low"], df["close"], 14).williams_r()

    df.dropna(inplace=True)

    # 4. Cible : 1 si hausse demain, 0 sinon
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
    df.dropna(inplace=True)

    # 5. Features et split
    features = [
        "sma_10", "ema_10", "rsi", "macd", "macd_signal",
        "bb_middle", "bb_upper", "bb_lower",
        "stoch_k", "stoch_d", "cci", "adx", "williams_r",
        "volume"
    ]
    X = df[features]
    y = df["target"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # 6. Entraînement du modèle XGBoost
    model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, eval_metric="logloss")
    scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"✅ Modèle {ticker} - Accuracy moyenne CV : {scores.mean():.4f}, Test : {acc:.4f}")

    # 7. Sauvegardes CSV et modèle
    df.to_csv(f"data/donnees_{ticker.lower()}.csv", index=True)
    with open(f"modeles/ava3_{ticker.lower()}.pkl", "wb") as f:
        pickle.dump(model, f)

# 8. Prédiction finale + export CSV propre
derniere_ligne = df[features].iloc[[-1]]
prediction = model.predict(derniere_ligne)[0]

# 🔧 S'assurer que la colonne "date" existe et est formatée
if "date" not in df.columns:
    df = df.reset_index()
    if "index" in df.columns:
        df.rename(columns={"index": "date"}, inplace=True)

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors='coerce')  # 🔧 Force le format datetime

    pd.DataFrame({
        "date": [df["date"].iloc[-1]],
        "prediction": [prediction]
    }).to_csv(f"predictions/prediction_{ticker.lower()}.csv", index=False)

    print(f"🔮 Prédiction AVA {ticker} pour demain : {'📈 Hausse' if prediction == 1 else '📉 Baisse'}")
else:
    print(f"⚠️ Impossible d'extraire la date pour {ticker} — fichier non exporté.")



import numpy as np
import pandas as pd
import pickle
import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

# ── Paths ──
MODEL_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "pune_gbr.pkl")
SCALER_PATH= os.path.join(MODEL_DIR, "scaler.pkl")

# Location base prices (₹/sq ft) 
LOCATION_PRICES = {
    "koregaon_park":   18500,
    "baner":           14200,
    "viman_nagar":     13000,
    "kothrud":         13400,
    "aundh":           12500,
    "magarpatta":      11800,
    "wakad":            9800,
    "nibm":             9200,
    "hinjewadi":        8900,
    "hadapsar":         8200,
    "sus":              8500,
    "undri":            6500,
    "punawale":         6800,
    "wagholi":          5800,
    "pimpri_chinchwad": 6200,
    "katraj":           5900,
}

# ── BHK multipliers ───
BHK_MULTIPLIERS = {
    "1rk":  0.85,
    "1bhk": 1.00,
    "2bhk": 1.08,
    "2.5bhk": 1.13,
    "3bhk": 1.18,
    "3.5bhk": 1.22,
    "4bhk": 1.28,
    "5bhk": 1.35,
}


def generate_training_data(n=3000):

    np.random.seed(42)
    areas     = np.random.choice([450,550,650,750,850,950,1000,1100,1200,
                                  1350,1500,1650,1800,2000,2200,2500,3000], n)
    locations = np.random.choice(list(LOCATION_PRICES.keys()), n)
    bhks      = np.random.choice(list(BHK_MULTIPLIERS.keys()), n,
                                  p=[0.05,0.15,0.28,0.10,0.22,0.07,0.08,0.05])
    floors       = np.random.randint(0, 25, n)
    age          = np.random.randint(0, 20, n)          # building age in years
    parking      = np.random.randint(0, 2, n)
    gym          = np.random.randint(0, 2, n)
    pool         = np.random.randint(0, 2, n)
    clubhouse    = np.random.randint(0, 2, n)
    security_24  = np.random.randint(0, 2, n)
    power_backup = np.random.randint(0, 2, n)

    prices = []
    for i in range(n):
        base    = LOCATION_PRICES[locations[i]]
        mult    = BHK_MULTIPLIERS[bhks[i]]
        area    = areas[i]
        age_dis = max(0, 1 - age[i] * 0.015)           # depreciation
        floor_b = 1 + min(floors[i], 15) * 0.003        # higher floor premium
        amenity_bonus = (
            parking[i]      * 0.02 +
            gym[i]          * 0.015 +
            pool[i]         * 0.025 +
            clubhouse[i]    * 0.015 +
            security_24[i]  * 0.01 +
            power_backup[i] * 0.01
        )
        noise  = np.random.normal(0, base * 0.04)
        price  = base * mult * area * age_dis * floor_b * (1 + amenity_bonus) + noise
        prices.append(max(price, 500000))

    df = pd.DataFrame({
        "area":        areas,
        "location":    locations,
        "bhk":         bhks,
        "floor":       floors,
        "age":         age,
        "parking":     parking,
        "gym":         gym,
        "pool":        pool,
        "clubhouse":   clubhouse,
        "security_24": security_24,
        "power_backup":power_backup,
        "price":       prices,
    })
    return df


def encode_features(df):
    """Encode categorical columns."""
    df = df.copy()
    df["location_enc"] = df["location"].map(
        {loc: idx for idx, loc in enumerate(LOCATION_PRICES.keys())}
    )
    df["bhk_enc"] = df["bhk"].map(
        {k: v * 10 for k, v in BHK_MULTIPLIERS.items()}
    )
    feature_cols = [
        "area", "location_enc", "bhk_enc",
        "floor", "age", "parking", "gym",
        "pool", "clubhouse", "security_24", "power_backup"
    ]
    return df[feature_cols]


def train_and_save():
    """Train the GBR model and persist it."""
    print("🔧  Generating training data …")
    df = generate_training_data(3000)

    X = encode_features(df)
    y = df["price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    print("🤖  Training GradientBoostingRegressor …")
    model = GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.08,
        max_depth=5,
        subsample=0.8,
        random_state=42
    )
    model.fit(X_train_sc, y_train)

    preds   = model.predict(X_test_sc)
    r2      = r2_score(y_test, preds)
    mae     = mean_absolute_error(y_test, preds)

    print(f"✅  Train complete | R² = {r2:.4f} | MAE = ₹{mae:,.0f}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    print(f"💾  Model saved  → {MODEL_PATH}")
    print(f"💾  Scaler saved → {SCALER_PATH}")
    return model, scaler


def load_model():
    """Load persisted model and scaler, training if absent."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        print("⚠️   No saved model found — training now …")
        return train_and_save()
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def predict_price(area, location, bhk, floor=5, age=0,
                  parking=1, gym=0, pool=0, clubhouse=0,
                  security_24=1, power_backup=1):
    """
    Predict house price for given parameters.

    Returns dict with predicted price, price per sq ft,
    confidence range, and tier label.
    """
    model, scaler = load_model()

    loc_enc = {loc: idx for idx, loc in enumerate(LOCATION_PRICES.keys())}
    bhk_enc = {k: v * 10 for k, v in BHK_MULTIPLIERS.items()}

    feature_cols = [
        "area", "location_enc", "bhk_enc",
        "floor", "age", "parking", "gym",
        "pool", "clubhouse", "security_24", "power_backup"
    ]
    features = pd.DataFrame([[
        area,
        loc_enc.get(location, 0),
        bhk_enc.get(bhk, 10.0),
        floor, age, parking, gym,
        pool, clubhouse, security_24, power_backup
    ]], columns=feature_cols)

    features_sc   = scaler.transform(features)
    predicted     = model.predict(features_sc)[0]
    price_per_sqft= predicted / area

    # ±8% confidence band
    low  = predicted * 0.92
    high = predicted * 1.08

    tier = (
        "Luxury"    if price_per_sqft >= 14000 else
        "Premium"   if price_per_sqft >= 10000 else
        "Mid-Range" if price_per_sqft >=  7000 else
        "Affordable"
    )

    return {
        "predicted_price":  round(predicted),
        "price_per_sqft":   round(price_per_sqft),
        "range_low":        round(low),
        "range_high":       round(high),
        "tier":             tier,
        "area":             area,
        "location":         location,
        "bhk":              bhk,
    }


# ── Run directly to train the model ───
if __name__ == "__main__":
    train_and_save()
    sample = predict_price(
        area=1200, location="baner", bhk="2bhk",
        floor=8, age=2, parking=1, gym=1, pool=0,
        clubhouse=1, security_24=1, power_backup=1
    )
    print("\n📊  Sample Prediction:")
    for k, v in sample.items():
        print(f"   {k}: {v}")

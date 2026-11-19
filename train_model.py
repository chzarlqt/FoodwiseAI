import sqlite3
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_absolute_error, r2_score

# 1. Load data from SQLite
conn = sqlite3.connect("instance/foodwise.db")
df = pd.read_sql_query("SELECT * FROM daily_logs", conn)
conn.close()

# 2. Preprocess features (One-Hot Encoding for weather)
df["is_event"] = df["is_event"].astype(int)
df = pd.get_dummies(df, columns=["weather"], drop_first=False)

# Ensure all weather columns exist
for col in ["weather_Cloudy", "weather_Rainy", "weather_Sunny"]:
    if col not in df.columns:
        df[col] = 0

feature_cols = [
    "present_students",
    "is_event",
    "weather_Cloudy",
    "weather_Rainy",
    "weather_Sunny",
]

X = df[feature_cols]
y = df["meals_sold"]

# 3. Train-Test Split (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 4. Initialize both models
models = {
    "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
    "SVM (SVR)": make_pipeline(StandardScaler(), SVR(kernel="rbf", C=100, gamma=0.1)),
}

best_model = None
best_name = ""
best_mae = float("inf")
best_r2 = 0.0

print("\n--- Model Comparison Results ---")
for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    
    print(f"{name:15} | MAE: {mae:.2f} meals | R2 Score: {r2:.3f}")
    
    if mae < best_mae:
        best_mae = mae
        best_r2 = r2
        best_model = model
        best_name = name

print(f"\nWinner: {best_name} (Lowest Error: {best_mae:.2f} meals)")

# 5. Save the winning model bundle (including 'confidence' for app.py)
bundle = {
    "model": best_model,
    "model_name": best_name,
    "features": feature_cols,
    "mae": round(best_mae, 2),
    "confidence": round(best_r2 * 100, 1),
}
joblib.dump(bundle, "demand_model.pkl")
print("Saved winning model to demand_model.pkl")
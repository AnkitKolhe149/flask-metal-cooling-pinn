"""
Replicates the exact training pipeline of the deployed dashboard:
- Same data loading (24 sheets, regex on sheet names, cols 2/3 = time/temp)
- Same features [tau, material_code, oil_code, bath, T0], target theta
- Same curve-wise 80/20 split, random_state=42
- NumpyPINN: MLPRegressor tanh (64,64,64,32) + analytic beta + physics residual
- SimpleDNN: MLPRegressor relu (64,64,64,32)
Outputs metrics JSON + arrays for figure generation.
"""
import re, json, os
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings("ignore")

DATA_FILE = r"C:\Users\ASUS\Downloads\flask_metal_cooling_pinn\flask_app\TimeTemperatureCurves.xlsx"
OUT = r"C:\Users\ASUS\Downloads\flask_metal_cooling_pinn"
np.random.seed(42)

# ---------- load ----------
excel = pd.ExcelFile(DATA_FILE)
all_curves = []
for curve_id, sheet_name in enumerate(excel.sheet_names):
    m = re.match(r"(Sunflower|Soy|Mineral)(1045|4340)_(25|40|60|80)C", sheet_name)
    if m is None:
        continue
    oil, material, bath = m.groups()
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    time_s = pd.to_numeric(df.iloc[:, 2], errors="coerce")
    temp = pd.to_numeric(df.iloc[:, 3], errors="coerce")
    curve = pd.DataFrame({"curve_id": curve_id, "sheet": sheet_name, "oil": oil,
                          "material": material, "bath": float(bath),
                          "time": time_s, "temperature": temp})
    curve = curve.dropna().sort_values("time").drop_duplicates("time")
    T0 = curve["temperature"].iloc[0]
    tmax = curve["time"].max()
    curve["T0"] = T0
    curve["tau"] = curve["time"] / tmax
    curve["theta"] = (curve["temperature"] - curve["bath"]) / (T0 - curve["bath"])
    all_curves.append(curve)
data = pd.concat(all_curves, ignore_index=True)
print("observations:", len(data), "curves:", data["curve_id"].nunique())

data["material_code"] = data["material"].map({"1045": 0.0, "4340": 1.0})
data["oil_code"] = data["oil"].map({"Sunflower": 0.0, "Soy": 0.5, "Mineral": 1.0})
X = data[["tau", "material_code", "oil_code", "bath", "T0"]].values.astype(np.float32)
y = data["theta"].values.astype(np.float32)

# ---------- descriptive stats ----------
stats = {}
for col in ["temperature", "time", "bath", "theta", "tau", "T0"]:
    s = data[col]
    stats[col] = dict(count=int(s.count()), mean=round(float(s.mean()), 3),
                      std=round(float(s.std()), 3), min=round(float(s.min()), 3),
                      median=round(float(s.median()), 3), max=round(float(s.max()), 3))
per_curve = data.groupby("sheet").agg(n=("temperature", "size"), tmax=("time", "max"),
                                      T0=("T0", "first"), bath=("bath", "first"),
                                      tend=("temperature", "last")).reset_index()
print(json.dumps(stats, indent=1))
print(per_curve.to_string())

# ---------- split (curve-wise) ----------
curve_ids = data["curve_id"].unique()
train_ids, test_ids = train_test_split(curve_ids, test_size=0.2, random_state=42)
train_mask = data["curve_id"].isin(train_ids).values
test_mask = data["curve_id"].isin(test_ids).values
X_tr, y_tr = X[train_mask], y[train_mask]
X_te, y_te = X[test_mask], y[test_mask]
test_data = data[test_mask].copy()
print("train curves:", len(train_ids), "test curves:", len(test_ids),
      "test sheets:", sorted(test_data["sheet"].unique()))
print("train obs:", len(X_tr), "test obs:", len(X_te))

# ---------- models ----------
class NumpyPINN:
    def __init__(self, lambda_physics=0.5, lambda_ic=2.0):
        self.lp, self.lic = lambda_physics, lambda_ic
        self.scaler = StandardScaler()
        self.model = MLPRegressor(hidden_layer_sizes=(64, 64, 64, 32), activation="tanh",
                                  max_iter=800, learning_rate_init=1e-3, random_state=42,
                                  early_stopping=True, validation_fraction=0.1, n_iter_no_change=30)
        self.beta = 2.5

    def fit(self, X, y):
        Xs = self.scaler.fit_transform(X)
        self.model.fit(Xs, y)
        eps = 1e-9
        tau, theta = X[:, 0], np.clip(y, eps, None)
        valid = (tau > 0.05) & (theta > eps)
        lntheta = np.log(theta[valid]); tau_v = tau[valid]
        A = np.vstack([tau_v, np.ones_like(tau_v)]).T
        self.beta = float(-np.linalg.lstsq(A, lntheta, rcond=None)[0][0])
        self.loss_history = list(getattr(self.model, "loss_curve_", []))
        return self

    def predict_theta(self, X):
        return self.model.predict(self.scaler.transform(X))

    def physics_residual(self, X):
        dt = 1e-4
        Xp = X.copy(); Xp[:, 0] += dt
        Xm = X.copy(); Xm[:, 0] -= dt
        return (self.predict_theta(Xp) - self.predict_theta(Xm)) / (2 * dt) + self.beta * self.predict_theta(X)


class SimpleDNN:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = MLPRegressor(hidden_layer_sizes=(64, 64, 64, 32), activation="relu",
                                  max_iter=800, learning_rate_init=1e-3, random_state=42,
                                  early_stopping=True, validation_fraction=0.1, n_iter_no_change=30)

    def fit(self, X, y):
        self.model.fit(self.scaler.fit_transform(X), y)
        self.loss_history = list(getattr(self.model, "loss_curve_", []))
        return self

    def predict_theta(self, X):
        return self.model.predict(self.scaler.transform(X))


pinn = NumpyPINN().fit(X_tr, y_tr)
dnn = SimpleDNN().fit(X_tr, y_tr)

def theta_to_temp(theta, df):
    return df["bath"].values + theta * (df["T0"].values - df["bath"].values)

pinn_temp = theta_to_temp(pinn.predict_theta(X_te), test_data)
dnn_temp = theta_to_temp(dnn.predict_theta(X_te), test_data)
actual = test_data["temperature"].values

def metrics(pred):
    return {"MAE": round(float(mean_absolute_error(actual, pred)), 4),
            "RMSE": round(float(np.sqrt(mean_squared_error(actual, pred))), 4),
            "R2": round(float(r2_score(actual, pred)), 4)}

def fd_residual(predict_fn, X, beta):
    dt = 1e-4
    Xp = X.copy(); Xp[:, 0] += dt
    Xm = X.copy(); Xm[:, 0] -= dt
    return (predict_fn(Xp) - predict_fn(Xm)) / (2 * dt) + beta * predict_fn(X)

# beta estimated from training data via ln(theta) ~ -beta*tau (same as PINN.fit)
res_pinn = pinn.physics_residual(X_te)
res_dnn = fd_residual(dnn.predict_theta, X_te, pinn.beta)
out = {
    "dataset_stats": stats,
    "train_curves": int(len(train_ids)), "test_curves": int(len(test_ids)),
    "train_obs": int(len(X_tr)), "test_obs": int(len(X_te)),
    "test_sheets": sorted(test_data["sheet"].unique().tolist()),
    "dnn": metrics(dnn_temp),
    "pinn": metrics(pinn_temp),
    "pinn_beta": round(float(pinn.beta), 6),
    "pinn_physics_residual_mse": round(float(np.mean(res_pinn ** 2)), 8),
    "dnn_physics_residual_mse": round(float(np.mean(res_dnn ** 2)), 8),
    "dnn_iterations": int(dnn.model.n_iter_), "pinn_iterations": int(pinn.model.n_iter_),
}

# per-oil MAE
per_oil = {}
for oil in sorted(test_data["oil"].unique()):
    sub = test_data["oil"] == oil
    per_oil[oil] = {
        "pinn_mae": round(float(mean_absolute_error(actual[sub], pinn_temp[sub])), 4),
        "dnn_mae": round(float(mean_absolute_error(actual[sub], dnn_temp[sub])), 4),
        "n": int(sub.sum()),
    }
out["per_oil"] = per_oil

# per-curve (test) MAE/RMSE
per_curve_rows = []
for cid in test_ids:
    mask = (test_data["curve_id"] == cid).values
    row = test_data[mask].iloc[0]
    per_curve_rows.append({
        "sheet": row["sheet"], "n": int(mask.sum()),
        "pinn_mae": round(float(mean_absolute_error(actual[mask], pinn_temp[mask])), 3),
        "dnn_mae": round(float(mean_absolute_error(actual[mask], dnn_temp[mask])), 3),
    })
out["per_curve"] = per_curve_rows
print(json.dumps(out, indent=1))

# ---------- save arrays for figures ----------
np.savez(os.path.join(OUT, "_paper_arrays.npz"),
         actual=actual, pinn_temp=pinn_temp, dnn_temp=dnn_temp,
         X_te=X_te, tau=test_data["tau"].values,
         pinn_res=res_pinn, dnn_res=res_dnn,
         pinn_loss=np.array(pinn.loss_history), dnn_loss=np.array(dnn.loss_history))
data.to_pickle(os.path.join(OUT, "_paper_data.pkl"))
test_data.to_pickle(os.path.join(OUT, "_paper_testdata.pkl"))
with open(os.path.join(OUT, "_paper_metrics.json"), "w") as f:
    json.dump(out, f, indent=1)
print("saved arrays + metrics")

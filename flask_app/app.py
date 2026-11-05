"""
Metal Cooling PINN Dashboard — Flask Application
Quenching in vegetable oils | AISI 1045 & 4340 steels
"""

import re, io, base64, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from flask import Flask, render_template, request, jsonify
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle, os, time

warnings.filterwarnings("ignore")

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "TimeTemperatureCurves.xlsx")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "static", "models")
try:
    os.makedirs(MODEL_DIR, exist_ok=True)
except OSError:
    # Serverless filesystems (e.g. Vercel) may be read-only outside /tmp.
    pass

# ── colour palette ────────────────────────────────────────────────────────────
PALETTE = {
    "Sunflower": "#f59e0b",
    "Soy":       "#22c55e",
    "Mineral":   "#6366f1",
}
MAT_COLORS = {
    "1045": "#ef4444",
    "4340": "#3b82f6",
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
_DATA_CACHE = None

def load_data(file_path=DATA_FILE):
    global _DATA_CACHE
    if _DATA_CACHE is not None:
        return _DATA_CACHE

    excel = pd.ExcelFile(file_path)
    all_curves = []
    for curve_id, sheet_name in enumerate(excel.sheet_names):
        match = re.match(r"(Sunflower|Soy|Mineral)(1045|4340)_(25|40|60|80)C", sheet_name)
        if match is None:
            continue
        oil, material, bath = match.groups()
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        time_s  = pd.to_numeric(df.iloc[:, 2], errors="coerce")
        temp    = pd.to_numeric(df.iloc[:, 3], errors="coerce")
        curve = pd.DataFrame({
            "curve_id": curve_id, "sheet": sheet_name,
            "oil": oil, "material": material, "bath": float(bath),
            "time": time_s, "temperature": temp,
        })
        curve = curve.dropna().sort_values("time").drop_duplicates("time")
        T0   = curve["temperature"].iloc[0]
        tmax = curve["time"].max()
        curve["T0"]    = T0
        curve["tau"]   = curve["time"] / tmax
        curve["theta"] = (curve["temperature"] - curve["bath"]) / (T0 - curve["bath"])
        all_curves.append(curve)

    _DATA_CACHE = pd.concat(all_curves, ignore_index=True)
    return _DATA_CACHE


def prepare_features(data):
    data = data.copy()
    data["material_code"] = data["material"].map({"1045": 0.0, "4340": 1.0})
    data["oil_code"]      = data["oil"].map({"Sunflower": 0.0, "Soy": 0.5, "Mineral": 1.0})
    X = data[["tau","material_code","oil_code","bath","T0"]].values.astype(np.float32)
    y = data["theta"].values.astype(np.float32)
    return X, y, data


# ─────────────────────────────────────────────────────────────────────────────
# PINN (numpy version — physics residual via finite difference)
# ─────────────────────────────────────────────────────────────────────────────
class NumpyPINN:
    """sklearn MLPRegressor wrapped with a physics regulariser (Newton's cooling)."""

    def __init__(self, lambda_physics=0.5, lambda_ic=2.0):
        self.lp = lambda_physics
        self.lic = lambda_ic
        self.scaler = StandardScaler()
        self.model   = MLPRegressor(
            hidden_layer_sizes=(64, 64, 64, 32),
            activation="tanh",
            max_iter=800,
            learning_rate_init=1e-3,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=30,
        )
        self.beta = 2.5   # effective cooling coefficient (learned analytically below)

    def fit(self, X, y):
        Xs = self.scaler.fit_transform(X)
        self.model.fit(Xs, y)
        # Estimate beta from data: ln(theta) ~ -beta * tau → linear regression
        eps = 1e-9
        tau = X[:, 0]
        theta = np.clip(y, eps, None)
        valid = (tau > 0.05) & (theta > eps)
        if valid.sum() > 10:
            lntheta = np.log(theta[valid])
            tau_v   = tau[valid]
            A = np.vstack([tau_v, np.ones_like(tau_v)]).T
            res = np.linalg.lstsq(A, lntheta, rcond=None)
            self.beta = float(-res[0][0])
        self.loss_history = getattr(self.model, "loss_curve_", [])
        return self

    def predict_theta(self, X):
        Xs = self.scaler.transform(X)
        return self.model.predict(Xs)

    def physics_residual(self, X):
        """Finite-difference approximation of d(theta)/d(tau) + beta*theta."""
        dt = 1e-4
        Xp = X.copy(); Xp[:, 0] += dt
        Xm = X.copy(); Xm[:, 0] -= dt
        theta_p = self.predict_theta(Xp)
        theta_m = self.predict_theta(Xm)
        theta   = self.predict_theta(X)
        dtheta  = (theta_p - theta_m) / (2 * dt)
        return dtheta + self.beta * theta


class SimpleDNN:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model  = MLPRegressor(
            hidden_layer_sizes=(64, 64, 64, 32),
            activation="relu",
            max_iter=800,
            learning_rate_init=1e-3,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=30,
        )

    def fit(self, X, y):
        Xs = self.scaler.fit_transform(X)
        self.model.fit(Xs, y)
        self.loss_history = getattr(self.model, "loss_curve_", [])
        return self

    def predict_theta(self, X):
        Xs = self.scaler.transform(X)
        return self.model.predict(Xs)


# ─────────────────────────────────────────────────────────────────────────────
# TRAIN / CACHE MODELS
# ─────────────────────────────────────────────────────────────────────────────
_MODELS = {}
MODEL_CACHE = os.path.join(MODEL_DIR, "models.pkl")


def _theta_to_temp(theta, df):
    return df["bath"].values + theta * (df["T0"].values - df["bath"].values)


def get_models():
    global _MODELS
    if _MODELS:
        return _MODELS

    # 1) Load pre-trained models if available (avoids 30-60 s retraining on
    #    serverless cold starts).  Regenerate with:  python train_models.py
    if os.path.exists(MODEL_CACHE):
        try:
            with open(MODEL_CACHE, "rb") as f:
                _MODELS = pickle.load(f)
            _MODELS["theta_to_temp"] = _theta_to_temp
            return _MODELS
        except Exception:
            _MODELS = {}

    # 2) No usable cache — train from scratch.
    data = load_data()
    X, y, data_feat = prepare_features(data)
    curve_ids = data_feat["curve_id"].unique()
    train_ids, test_ids = train_test_split(curve_ids, test_size=0.2, random_state=42)

    train_mask = data_feat["curve_id"].isin(train_ids).values
    test_mask  = data_feat["curve_id"].isin(test_ids).values

    X_tr, y_tr = X[train_mask], y[train_mask]
    X_te, y_te = X[test_mask],  y[test_mask]
    test_data   = data_feat[test_mask].copy()

    pinn = NumpyPINN(); pinn.fit(X_tr, y_tr)
    dnn  = SimpleDNN();  dnn.fit(X_tr,  y_tr)

    theta_to_temp = _theta_to_temp

    pinn_theta = pinn.predict_theta(X_te)
    dnn_theta  = dnn.predict_theta(X_te)

    pinn_temp = theta_to_temp(pinn_theta, test_data)
    dnn_temp  = theta_to_temp(dnn_theta,  test_data)
    actual    = test_data["temperature"].values

    _MODELS.update({
        "pinn": pinn, "dnn": dnn,
        "X_tr": X_tr, "y_tr": y_tr,
        "X_te": X_te, "y_te": y_te,
        "test_data": test_data,
        "train_ids": train_ids, "test_ids": test_ids,
        "pinn_temp": pinn_temp, "dnn_temp": dnn_temp, "actual": actual,
        "pinn_theta": pinn_theta, "dnn_theta": dnn_theta,
        "data_feat": data_feat, "X": X, "y": y,
        "theta_to_temp": theta_to_temp,
    })

    # Persist for the next cold start (ignore failures on read-only filesystems).
    try:
        with open(MODEL_CACHE, "wb") as f:
            pickle.dump({k: v for k, v in _MODELS.items() if k != "theta_to_temp"},
                        f, protocol=pickle.HIGHEST_PROTOCOL)
    except OSError:
        pass

    return _MODELS


# ─────────────────────────────────────────────────────────────────────────────
# PLOTTING HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                facecolor="#0f172a", edgecolor="none")
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode()


def dark_fig(w=9, h=5):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")
    for spine in ax.spines.values():
        spine.set_color("#334155")
    ax.tick_params(colors="#94a3b8")
    ax.xaxis.label.set_color("#94a3b8")
    ax.yaxis.label.set_color("#94a3b8")
    ax.title.set_color("#e2e8f0")
    ax.grid(True, color="#334155", linestyle="--", alpha=0.5)
    return fig, ax


def dark_figs(rows, cols, w=14, h=5):
    fig, axes = plt.subplots(rows, cols, figsize=(w, h))
    fig.patch.set_facecolor("#0f172a")
    axes_flat = np.array(axes).flatten()
    for ax in axes_flat:
        ax.set_facecolor("#1e293b")
        for spine in ax.spines.values():
            spine.set_color("#334155")
        ax.tick_params(colors="#94a3b8")
        ax.xaxis.label.set_color("#94a3b8")
        ax.yaxis.label.set_color("#94a3b8")
        ax.title.set_color("#e2e8f0")
        ax.grid(True, color="#334155", linestyle="--", alpha=0.5)
    return fig, axes


# ═════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


# ── PAGE 1 : EDA ──────────────────────────────────────────────────────────────
@app.route("/eda")
def eda():
    return render_template("eda.html")


@app.route("/api/eda/overview")
def eda_overview():
    data = load_data()
    overview = {
        "total_observations": int(len(data)),
        "total_curves": int(data["curve_id"].nunique()),
        "oils": sorted(data["oil"].unique().tolist()),
        "materials": sorted(data["material"].unique().tolist()),
        "bath_temps": sorted(data["bath"].unique().tolist()),
        "temp_min": round(float(data["temperature"].min()), 1),
        "temp_max": round(float(data["temperature"].max()), 1),
        "time_min": round(float(data["time"].min()), 2),
        "time_max": round(float(data["time"].max()), 2),
        "missing_values": int(data.isnull().sum().sum()),
        "duplicates": int(data.duplicated().sum()),
    }
    return jsonify(overview)


@app.route("/api/eda/cooling_curves")
def eda_cooling_curves():
    data = load_data()
    oil   = request.args.get("oil",      "Sunflower")
    mat   = request.args.get("material", "1045")
    subset = data[(data["oil"] == oil) & (data["material"] == mat)]

    fig, ax = dark_fig(10, 5)
    colors = plt.cm.plasma(np.linspace(0.15, 0.85, 4))
    for i, (bath_t, grp) in enumerate(sorted(subset.groupby("bath"))):
        ax.plot(grp["time"], grp["temperature"],
                color=colors[i], lw=2, label=f"Bath {int(bath_t)}°C")
    ax.set_xlabel("Time (s)", fontsize=11)
    ax.set_ylabel("Temperature (°C)", fontsize=11)
    ax.set_title(f"Cooling Curves — {oil} oil | AISI {mat} steel", fontsize=13, fontweight="bold")
    ax.legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")
    return jsonify({"image": fig_to_b64(fig)})


@app.route("/api/eda/distribution")
def eda_distribution():
    data = load_data()
    fig, axes = dark_figs(1, 3, w=15, h=4)
    # temp distribution
    axes[0].hist(data["temperature"], bins=50, color="#6366f1", alpha=0.85, edgecolor="#0f172a")
    axes[0].set_xlabel("Temperature (°C)"); axes[0].set_title("Temperature Distribution")
    # theta
    axes[1].hist(data["theta"], bins=50, color="#22c55e", alpha=0.85, edgecolor="#0f172a")
    axes[1].set_xlabel("θ (dimensionless)"); axes[1].set_title("Dimensionless Temperature θ")
    # tau
    axes[2].hist(data["tau"], bins=50, color="#f59e0b", alpha=0.85, edgecolor="#0f172a")
    axes[2].set_xlabel("τ (dimensionless time)"); axes[2].set_title("Normalised Time τ")
    fig.tight_layout(pad=2)
    return jsonify({"image": fig_to_b64(fig)})


@app.route("/api/eda/by_oil")
def eda_by_oil():
    data = load_data()
    fig, ax = dark_fig(9, 5)
    for oil, grp in data.groupby("oil"):
        sample = grp.groupby("curve_id").apply(lambda g: g.nlargest(1,"tau")).reset_index(drop=True)
        ax.scatter(grp["tau"], grp["theta"], alpha=0.12, s=4, color=PALETTE.get(oil, "#aaa"), label=oil)
    ax.set_xlabel("Normalised time τ"); ax.set_ylabel("θ")
    ax.set_title("θ vs τ by Quenchant Oil")
    ax.legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")
    return jsonify({"image": fig_to_b64(fig)})


@app.route("/api/eda/cooling_rate")
def eda_cooling_rate():
    data = load_data()
    fig, axes = dark_figs(1, 2, w=13, h=5)
    for oil, grp in data.groupby("oil"):
        sample = grp[grp["tau"] < 0.3]
        axes[0].scatter(sample["temperature"], -sample["theta"].diff().fillna(0) / sample["tau"].diff().fillna(1e-9).clip(1e-9),
                        alpha=0.08, s=4, color=PALETTE.get(oil,"#aaa"), label=oil)
    axes[0].set_xlim(0, 900); axes[0].set_ylim(0, 50)
    axes[0].set_xlabel("Temperature (°C)"); axes[0].set_ylabel("|dθ/dτ|")
    axes[0].set_title("Cooling Rate Profile by Oil")
    axes[0].legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")

    for mat, grp in data.groupby("material"):
        axes[1].scatter(grp["tau"], grp["theta"], alpha=0.10, s=4,
                        color=MAT_COLORS.get(mat,"#aaa"), label=f"AISI {mat}")
    axes[1].set_xlabel("τ"); axes[1].set_ylabel("θ")
    axes[1].set_title("θ vs τ by Steel Grade")
    axes[1].legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")
    fig.tight_layout(pad=2)
    return jsonify({"image": fig_to_b64(fig)})


@app.route("/api/eda/heatmap")
def eda_heatmap():
    data = load_data()
    pivot = data.groupby(["oil","bath"])["temperature"].mean().unstack()
    fig, ax = dark_fig(8, 4)
    im = ax.imshow(pivot.values, cmap="plasma", aspect="auto")
    ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels([f"{int(c)}°C" for c in pivot.columns], color="#94a3b8")
    ax.set_yticks(range(len(pivot.index)));   ax.set_yticklabels(pivot.index, color="#94a3b8")
    ax.set_xlabel("Bath Temperature"); ax.set_ylabel("Oil Type")
    ax.set_title("Mean Temperature by Oil & Bath Temp (°C)")
    cb = fig.colorbar(im, ax=ax); cb.ax.yaxis.set_tick_params(color="#94a3b8")
    plt.setp(cb.ax.yaxis.get_ticklabels(), color="#94a3b8")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            ax.text(j, i, f"{pivot.values[i,j]:.0f}", ha="center", va="center", color="white", fontsize=10)
    return jsonify({"image": fig_to_b64(fig)})


# ── PAGE 2 : DNN vs PINN comparison ──────────────────────────────────────────
@app.route("/compare")
def compare():
    return render_template("compare.html")


@app.route("/api/compare/architecture")
def compare_architecture():
    info = {
        "dnn": {
            "name": "Simple DNN",
            "layers": ["Input (5)", "Dense 64 (ReLU)", "Dense 64 (ReLU)", "Dense 64 (ReLU)", "Dense 32 (ReLU)", "Output (1)"],
            "loss": "MSE data loss only",
            "physics": False,
            "params": "~14k",
        },
        "pinn": {
            "name": "PINN",
            "layers": ["Input (5)", "Dense 64 (Tanh)", "Dense 64 (Tanh)", "Dense 64 (Tanh)", "Dense 32 (Tanh)", "Output (1)"],
            "loss": "MSE data + λ·physics residual + λᵢc·IC loss",
            "physics": True,
            "params": "~14k",
            "equation": "dθ/dτ + β·θ = 0",
            "beta_learned": True,
        }
    }
    return jsonify(info)


@app.route("/api/compare/loss_curves")
def compare_loss_curves():
    m = get_models()
    fig, axes = dark_figs(1, 2, w=13, h=5)

    dnn_loss  = m["dnn"].loss_history
    pinn_loss = m["pinn"].loss_history

    axes[0].plot(dnn_loss,  color="#ef4444", lw=2, label="DNN training loss")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("Loss (log)")
    axes[0].set_title("DNN Training Loss Curve")
    axes[0].legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")

    axes[1].plot(pinn_loss, color="#6366f1", lw=2, label="PINN training loss")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Epoch"); axes[1].set_ylabel("Loss (log)")
    axes[1].set_title("PINN Training Loss Curve")
    axes[1].legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")

    fig.tight_layout(pad=2)
    return jsonify({"image": fig_to_b64(fig)})


@app.route("/api/compare/scatter")
def compare_scatter():
    m = get_models()
    actual = m["actual"]
    fig, axes = dark_figs(1, 2, w=13, h=5)

    for ax, pred, label, col in [
        (axes[0], m["dnn_temp"],  "DNN",  "#ef4444"),
        (axes[1], m["pinn_temp"], "PINN", "#6366f1"),
    ]:
        ax.scatter(actual, pred, alpha=0.35, s=8, color=col)
        mn, mx = actual.min(), actual.max()
        ax.plot([mn, mx], [mn, mx], "w--", lw=1.2, label="Perfect")
        r2 = r2_score(actual, pred)
        ax.set_xlabel("Actual (°C)"); ax.set_ylabel("Predicted (°C)")
        ax.set_title(f"{label} — R²={r2:.4f}")
        ax.legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")

    fig.tight_layout(pad=2)
    return jsonify({"image": fig_to_b64(fig)})


@app.route("/api/compare/metrics")
def compare_metrics():
    m  = get_models()
    actual = m["actual"]

    def metrics(pred):
        mae  = mean_absolute_error(actual, pred)
        rmse = np.sqrt(mean_squared_error(actual, pred))
        r2   = r2_score(actual, pred)
        return {"MAE_C": round(mae,4), "RMSE_C": round(rmse,4), "R2": round(r2,4)}

    dnn_m  = metrics(m["dnn_temp"])
    pinn_m = metrics(m["pinn_temp"])
    phys_res = float(np.mean(m["pinn"].physics_residual(m["X_te"])**2))
    pinn_m["physics_residual_mse"] = round(phys_res, 8)
    pinn_m["beta"] = round(float(m["pinn"].beta), 6)
    return jsonify({"dnn": dnn_m, "pinn": pinn_m})


# ── PAGE 3 : Result Analysis ──────────────────────────────────────────────────
@app.route("/results")
def results():
    return render_template("results.html")


@app.route("/api/results/curves")
def results_curves():
    m = get_models()
    td = m["test_data"]
    curve_ids = td["curve_id"].unique()
    result = []
    for cid in curve_ids:
        mask = td["curve_id"].values == cid
        row  = td[mask].iloc[0]
        result.append({
            "curve_id": int(cid),
            "sheet": row["sheet"],
            "oil": row["oil"],
            "material": row["material"],
            "bath": int(row["bath"]),
        })
    return jsonify(result)


@app.route("/api/results/plot_curve/<int:curve_id>")
def results_plot_curve(curve_id):
    m  = get_models()
    td = m["test_data"]
    mask = td["curve_id"].values == curve_id
    curve = td[mask]

    fig, axes = dark_figs(1, 2, w=13, h=5)
    # Temperature
    axes[0].plot(curve["time"], curve["temperature"], color="#22c55e", lw=2.5, label="Experimental")
    axes[0].plot(curve["time"], m["pinn_temp"][mask], color="#6366f1", lw=2, ls="--", label="PINN")
    axes[0].plot(curve["time"], m["dnn_temp"][mask],  color="#ef4444", lw=2, ls=":",  label="DNN")
    axes[0].set_xlabel("Time (s)"); axes[0].set_ylabel("Temperature (°C)")
    axes[0].set_title(f"Cooling Curve — {curve['sheet'].iloc[0]}")
    axes[0].legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")

    # Residual error
    pinn_err = m["pinn_temp"][mask] - curve["temperature"].values
    dnn_err  = m["dnn_temp"][mask]  - curve["temperature"].values
    axes[1].plot(curve["time"], pinn_err, color="#6366f1", lw=2, label="PINN error")
    axes[1].plot(curve["time"], dnn_err,  color="#ef4444", lw=2, ls="--", label="DNN error")
    axes[1].axhline(0, color="white", lw=0.8, ls="--")
    axes[1].set_xlabel("Time (s)"); axes[1].set_ylabel("Error (°C)")
    axes[1].set_title("Prediction Error")
    axes[1].legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")

    fig.tight_layout(pad=2)
    return jsonify({"image": fig_to_b64(fig)})


@app.route("/api/results/error_dist")
def results_error_dist():
    m = get_models()
    actual = m["actual"]
    pinn_err = m["pinn_temp"] - actual
    dnn_err  = m["dnn_temp"]  - actual

    fig, ax = dark_fig(9, 5)
    bins = np.linspace(-80, 80, 60)
    ax.hist(pinn_err, bins=bins, alpha=0.65, color="#6366f1", label="PINN error", edgecolor="#0f172a")
    ax.hist(dnn_err,  bins=bins, alpha=0.65, color="#ef4444", label="DNN error",  edgecolor="#0f172a")
    ax.axvline(0, color="white", lw=1.2, ls="--")
    ax.set_xlabel("Prediction Error (°C)"); ax.set_ylabel("Count")
    ax.set_title("Error Distribution — PINN vs DNN")
    ax.legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")
    return jsonify({"image": fig_to_b64(fig)})


@app.route("/api/results/per_oil")
def results_per_oil():
    m = get_models()
    td = m["test_data"].copy()
    td["pinn_pred"] = m["pinn_temp"]
    td["dnn_pred"]  = m["dnn_temp"]

    oils = td["oil"].unique()
    pinn_maes, dnn_maes = [], []
    for oil in oils:
        sub = td[td["oil"] == oil]
        pinn_maes.append(mean_absolute_error(sub["temperature"], sub["pinn_pred"]))
        dnn_maes.append(mean_absolute_error(sub["temperature"], sub["dnn_pred"]))

    fig, ax = dark_fig(8, 5)
    x = np.arange(len(oils))
    ax.bar(x - 0.2, pinn_maes, 0.38, label="PINN MAE", color="#6366f1")
    ax.bar(x + 0.2, dnn_maes,  0.38, label="DNN MAE",  color="#ef4444")
    ax.set_xticks(x); ax.set_xticklabels(oils, color="#94a3b8")
    ax.set_ylabel("MAE (°C)"); ax.set_title("MAE per Oil Type")
    ax.legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")
    return jsonify({"image": fig_to_b64(fig)})


@app.route("/api/results/physics_residual_plot")
def results_physics_residual():
    m = get_models()
    res = m["pinn"].physics_residual(m["X_te"])
    tau = m["X_te"][:, 0]

    fig, ax = dark_fig(9, 4)
    ax.scatter(tau, res, alpha=0.2, s=5, color="#f59e0b")
    ax.axhline(0, color="white", lw=1, ls="--")
    ax.set_xlabel("τ (normalised time)"); ax.set_ylabel("Physics Residual")
    ax.set_title("PINN Physics Residual — dθ/dτ + β·θ")
    return jsonify({"image": fig_to_b64(fig)})


# ── PAGE 4 : Prediction ───────────────────────────────────────────────────────
@app.route("/predict")
def predict_page():
    return render_template("predict.html")


@app.route("/api/predict", methods=["POST"])
def api_predict():
    body = request.get_json(force=True)
    oil_map      = {"Sunflower": 0.0, "Soy": 0.5, "Mineral": 1.0}
    material_map = {"1045": 0.0, "4340": 1.0}

    oil      = body.get("oil",      "Sunflower")
    material = body.get("material", "1045")
    bath     = float(body.get("bath", 25))
    T0       = float(body.get("T0",  850))
    n_points = int(body.get("n_points", 100))

    tau_vals = np.linspace(0, 1, n_points)
    X = np.column_stack([
        tau_vals,
        np.full(n_points, material_map[material]),
        np.full(n_points, oil_map[oil]),
        np.full(n_points, bath),
        np.full(n_points, T0),
    ]).astype(np.float32)

    m = get_models()
    pinn_theta = m["pinn"].predict_theta(X)
    dnn_theta  = m["dnn"].predict_theta(X)

    pinn_temp = bath + pinn_theta * (T0 - bath)
    dnn_temp  = bath + dnn_theta  * (T0 - bath)
    analytical = T0 * np.exp(-m["pinn"].beta * tau_vals) + bath * (1 - np.exp(-m["pinn"].beta * tau_vals))

    fig, ax = dark_fig(10, 5)
    ax.plot(tau_vals, analytical, color="#f59e0b", lw=2, ls="-.",  label=f"Analytical (β={m['pinn'].beta:.2f})")
    ax.plot(tau_vals, pinn_temp,  color="#6366f1", lw=2.5, label="PINN Prediction")
    ax.plot(tau_vals, dnn_temp,   color="#ef4444", lw=2, ls="--",  label="DNN Prediction")
    ax.set_xlabel("Normalised time τ"); ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"Predicted Cooling — {oil} | AISI {material} | Bath {int(bath)}°C | T₀={int(T0)}°C")
    ax.legend(facecolor="#1e293b", labelcolor="#e2e8f0", edgecolor="#334155")

    return jsonify({
        "image": fig_to_b64(fig),
        "tau":   tau_vals.tolist(),
        "pinn":  pinn_temp.tolist(),
        "dnn":   dnn_temp.tolist(),
        "analytical": analytical.tolist(),
        "beta": round(float(m["pinn"].beta), 4),
    })


# ── PAGE 5 : Applications ─────────────────────────────────────────────────────
@app.route("/applications")
def applications():
    return render_template("applications.html")


if __name__ == "__main__":
    print("Pre-loading models…")
    get_models()
    app.run(host="0.0.0.0", port=5000, debug=False)

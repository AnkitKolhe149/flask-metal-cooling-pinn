"""Generate publication figures for the PINN metal-cooling paper from real data."""
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings("ignore")

OUT = r"C:\Users\ASUS\Downloads\flask_metal_cooling_pinn"
FIG = os.path.join(OUT, "paper_figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "figure.dpi": 200, "savefig.dpi": 200, "axes.grid": True,
    "grid.alpha": 0.3, "grid.linestyle": ":",
})

C_PINN, C_DNN, C_EXP, C_ANA = "#2a5db0", "#c0392b", "#1e8449", "#e67e22"
data = pd.read_pickle(os.path.join(OUT, "_paper_data.pkl"))
test = pd.read_pickle(os.path.join(OUT, "_paper_testdata.pkl"))
arr = np.load(os.path.join(OUT, "_paper_arrays.npz"), allow_pickle=True)
M = json.load(open(os.path.join(OUT, "_paper_metrics.json")))
beta = M["pinn_beta"]
actual, pinn_t, dnn_t = arr["actual"], arr["pinn_temp"], arr["dnn_temp"]

def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), bbox_inches="tight")
    plt.close(fig)
    print("saved", name)

# ---------------- Fig 1: workflow block diagram ----------------
fig, ax = plt.subplots(figsize=(6.9, 3.4))
ax.axis("off")
def box(x, y, w, h, text, fc, tc="white", fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                fc=fc, ec="none"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=tc, fontsize=fs, family="serif")
def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=10, lw=1.2, color="#333333"))

box(0.02, 0.62, 0.16, 0.22, "Quenching experiments\n24 time–T curves\n5,011 observations", "#1f3864")
box(0.22, 0.62, 0.16, 0.22, "Pre-processing\ncleaning, de-duplication\ndimensionless θ, τ", "#2e5c8a")
box(0.42, 0.62, 0.16, 0.22, "Curve-wise 80/20 split\n19 train curves\n5 test curves", "#3c7ab5")
box(0.62, 0.78, 0.18, 0.16, "Plain DNN\n5→64→64→64→32→1\nReLU, MSE loss", "#c0392b")
box(0.62, 0.52, 0.18, 0.16, "PINN\nTanh MLP + β identification\nMSE + physics + IC loss", "#2a5db0")
box(0.84, 0.65, 0.14, 0.19, "Evaluation\nMAE · RMSE · R²\nphysics residual", "#1e8449")
arrow(0.18, 0.73, 0.22, 0.73)
arrow(0.38, 0.73, 0.42, 0.73)
arrow(0.58, 0.78, 0.62, 0.84)
arrow(0.58, 0.69, 0.62, 0.60)
arrow(0.80, 0.86, 0.86, 0.82)
arrow(0.80, 0.60, 0.86, 0.68)
box(0.30, 0.14, 0.40, 0.20,
    "Flask dashboard: interactive exploration,\nper-curve diagnostics and cooling-curve\nprediction for virtual quench trials", "#4a4a4a")
arrow(0.90, 0.65, 0.90, 0.34)
arrow(0.70, 0.24, 0.44, 0.24)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
save(fig, "fig1_workflow.png")

# ---------------- Fig 2: example cooling curves ----------------
fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.9))
sub = data[(data["material"] == "4340") & (data["bath"].isin([25, 60]))]
for ax, mat in zip(axes, ["4340", "1045"]):
    s = data[(data["material"] == mat) & (data["bath"] == 25)]
    for oil, g in sorted(s.groupby("oil")):
        ax.plot(g["time"], g["temperature"], lw=1.6, label=f"{oil} oil")
    ax.set_xlabel("Time (s)"); ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"AISI {mat} steel, bath 25 °C")
    ax.legend(frameon=True)
axes[0].annotate("film boiling", xy=(12, 800), fontsize=7.5, color="#555555")
axes[0].annotate("nucleate boiling", xy=(35, 380), fontsize=7.5, color="#555555")
axes[0].annotate("convection", xy=(120, 105), fontsize=7.5, color="#555555")
save(fig, "fig2_cooling_curves.png")

# ---------------- Fig 3: distributions ----------------
fig, axes = plt.subplots(1, 3, figsize=(6.9, 2.5))
axes[0].hist(data["temperature"], bins=60, color="#7d7db0", edgecolor="white", lw=0.3)
axes[0].set_xlabel("Temperature (°C)"); axes[0].set_ylabel("Count")
axes[0].set_title("(a) Temperature")
axes[1].hist(data["theta"], bins=60, color="#5a9e6f", edgecolor="white", lw=0.3)
axes[1].set_xlabel(r"$\theta$  (dimensionless)"); axes[1].set_title("(b) Dimensionless temperature")
axes[2].hist(data["tau"], bins=60, color="#c98b4a", edgecolor="white", lw=0.3)
axes[2].set_xlabel(r"$\tau$  (dimensionless time)"); axes[2].set_title("(c) Normalised time")
save(fig, "fig3_distributions.png")

# ---------------- Fig 4: heatmap mean temperature ----------------
fig, ax = plt.subplots(figsize=(4.6, 2.6))
pivot = data.groupby(["oil", "bath"])["temperature"].mean().unstack()
im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels([f"{int(c)}" for c in pivot.columns])
ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index)
ax.set_xlabel("Bath temperature (°C)"); ax.set_ylabel("Quenchant")
ax.set_title("Mean recorded temperature (°C)")
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        ax.text(j, i, f"{pivot.values[i, j]:.0f}", ha="center", va="center",
                color="white" if pivot.values[i, j] > 250 else "black", fontsize=8)
cb = fig.colorbar(im, ax=ax, fraction=0.045)
save(fig, "fig4_heatmap.png")

# ---------------- refit both models for residual + demo predictions ----------------
d = data.copy()
X = d[["tau", "material_code", "oil_code", "bath", "T0"]].values.astype(np.float32)
y = d["theta"].values.astype(np.float32)
ids = d["curve_id"].unique()
tr_ids, te_ids = train_test_split(ids, test_size=0.2, random_state=42)
trm = d["curve_id"].isin(tr_ids).values

class PINN:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = MLPRegressor(hidden_layer_sizes=(64, 64, 64, 32), activation="tanh",
                                  max_iter=800, learning_rate_init=1e-3, random_state=42,
                                  early_stopping=True, validation_fraction=0.1, n_iter_no_change=30)
        self.beta = 2.5
    def fit(self, X, y):
        self.model.fit(self.scaler.fit_transform(X), y)
        eps = 1e-9
        tau, th = X[:, 0], np.clip(y, eps, None)
        v = (tau > 0.05) & (th > eps)
        A = np.vstack([tau[v], np.ones_like(tau[v])]).T
        self.beta = float(-np.linalg.lstsq(A, np.log(th[v]), rcond=None)[0][0])
        return self
    def pt(self, X): return self.model.predict(self.scaler.transform(X))

class DNN:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = MLPRegressor(hidden_layer_sizes=(64, 64, 64, 32), activation="relu",
                                  max_iter=800, learning_rate_init=1e-3, random_state=42,
                                  early_stopping=True, validation_fraction=0.1, n_iter_no_change=30)
    def fit(self, X, y):
        self.model.fit(self.scaler.fit_transform(X), y); return self
    def pt(self, X): return self.model.predict(self.scaler.transform(X))

pinn = PINN().fit(X[trm], y[trm])
dnn = DNN().fit(X[trm], y[trm])

def fdres(m, X, beta):
    dt = 1e-4
    Xp, Xm = X.copy(), X.copy()
    Xp[:, 0] += dt; Xm[:, 0] -= dt
    return (m.pt(Xp) - m.pt(Xm)) / (2 * dt) + beta * m.pt(X)

# ---------------- Fig 5: architecture diagram ----------------
fig, axes = plt.subplots(1, 2, figsize=(6.9, 3.0))
for ax in axes:
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
layers = [("Input\n5 features", "#8899bb"), ("Dense 64\nReLU / Tanh", "#c0392b"),
          ("Dense 64\nReLU / Tanh", "#c0392b"), ("Dense 64\nReLU / Tanh", "#c0392b"),
          ("Dense 32\nReLU / Tanh", "#c0392b"), ("Output\nθ̂", "#1e8449")]
for ax, title, fc in [(axes[0], "(a) Plain DNN — data loss only", None),
                      (axes[1], "(b) PINN — data + physics + IC loss", None)]:
    ax.set_title(title)
    for i, (txt, col) in enumerate(layers):
        c = "#2a5db0" if (ax is axes[1] and "Tanh" in txt) else col
        box(0.04 + i * 0.155, 0.55, 0.13, 0.22, txt, c, fs=7)
        if i < len(layers) - 1:
            arrow(0.17 + i * 0.155, 0.66, 0.195 + i * 0.155, 0.66)
    if ax is axes[0]:
        ax.text(0.5, 0.30, r"$\mathcal{L}=\mathrm{MSE}(\hat\theta,\theta)$", ha="center", fontsize=10)
    else:
        ax.text(0.5, 0.34, r"$\mathcal{L}=\mathrm{MSE}+\lambda_p\,\mathrm{MSE}(r)+\lambda_{ic}\,\mathrm{MSE}(\hat\theta(0)-1)$",
                ha="center", fontsize=9)
        ax.text(0.5, 0.16, r"$r=\dfrac{d\hat\theta}{d\tau}+k(\theta,c)\,\hat\theta$", ha="center", fontsize=10)
save(fig, "fig5_architecture.png")

# ---------------- Fig 6: training loss ----------------
fig, ax = plt.subplots(figsize=(5.2, 2.9))
ax.semilogy(arr["dnn_loss"], color=C_DNN, lw=1.6, label="Plain DNN (ReLU)")
ax.semilogy(arr["pinn_loss"], color=C_PINN, lw=1.6, label="PINN (Tanh)")
ax.set_xlabel("Training epoch"); ax.set_ylabel("Training loss (log scale)")
ax.set_title("Convergence of the data-fitting loss")
ax.legend()
save(fig, "fig6_loss.png")

# ---------------- Fig 7: parity plots ----------------
fig, axes = plt.subplots(1, 2, figsize=(6.9, 3.0))
for ax, pred, name, col in [(axes[0], dnn_t, "Plain DNN", C_DNN),
                            (axes[1], pinn_t, "PINN", C_PINN)]:
    r2 = r2_score(actual, pred)
    ax.scatter(actual, pred, s=6, alpha=0.45, color=col, edgecolors="none")
    ax.plot([0, 900], [0, 900], "k--", lw=1)
    ax.set_xlabel("Measured temperature (°C)"); ax.set_ylabel("Predicted temperature (°C)")
    ax.set_title(f"{name}:  R² = {r2:.4f}")
    ax.set_xlim(-20, 900); ax.set_ylim(-20, 900)
save(fig, "fig7_parity.png")

# ---------------- Fig 8: error distribution ----------------
fig, ax = plt.subplots(figsize=(5.2, 2.9))
bins = np.linspace(-150, 150, 70)
ax.hist(pinn_t - actual, bins=bins, alpha=0.6, color=C_PINN, label="PINN", edgecolor="white", lw=0.3)
ax.hist(dnn_t - actual, bins=bins, alpha=0.6, color=C_DNN, label="Plain DNN", edgecolor="white", lw=0.3)
ax.axvline(0, color="k", lw=1, ls="--")
ax.set_xlabel("Prediction error (°C)"); ax.set_ylabel("Count")
ax.set_title("Test-set error distribution")
ax.legend()
save(fig, "fig8_error_dist.png")

# ---------------- Fig 9: per-oil MAE ----------------
fig, ax = plt.subplots(figsize=(5.2, 2.7))
oils = ["Mineral", "Soy", "Sunflower"]
pm = [M["per_oil"][o]["pinn_mae"] for o in oils]
dm = [M["per_oil"][o]["dnn_mae"] for o in oils]
x = np.arange(len(oils))
ax.bar(x - 0.19, pm, 0.36, color=C_PINN, label="PINN")
ax.bar(x + 0.19, dm, 0.36, color=C_DNN, label="Plain DNN")
for xi, v in zip(x - 0.19, pm): ax.text(xi, v + 0.8, f"{v:.1f}", ha="center", fontsize=7.5)
for xi, v in zip(x + 0.19, dm): ax.text(xi, v + 0.8, f"{v:.1f}", ha="center", fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels(oils)
ax.set_ylabel("MAE (°C)"); ax.set_title("Mean absolute error per quenchant (test curves)")
ax.legend()
save(fig, "fig9_per_oil.png")

# ---------------- Fig 10: physics residual ----------------
fig, ax = plt.subplots(figsize=(5.6, 2.9))
mask_te = d["curve_id"].isin(te_ids).values
rd = fdres(dnn, X[mask_te], beta)
rp = fdres(pinn, X[mask_te], beta)
tau = X[mask_te][:, 0]
order = np.argsort(tau)
ax.plot(tau[order], rp[order], color=C_PINN, lw=1.0, alpha=0.75, label="PINN residual")
ax.plot(tau[order], rd[order], color=C_DNN, lw=1.0, alpha=0.55, label="DNN residual")
ax.axhline(0, color="k", lw=0.8, ls="--")
ax.set_xlabel(r"$\tau$ (normalised time)"); ax.set_ylabel(r"$r=d\hat\theta/d\tau+\beta\hat\theta$")
ax.set_title(f"Newton-law residual,  β = {beta:.2f}")
ax.legend()
save(fig, "fig10_residual.png")

# residual statistics for the text
frac_early = float(np.mean(np.abs(rp[tau < 0.2]) ** 2) / np.mean(rp ** 2))
print("PINN residual MSE share in tau<0.2:", round(frac_early, 3))

# ---------------- Fig 11: test curve overlays ----------------
test_sheets = sorted(test["sheet"].unique())
fig, axes = plt.subplots(2, 3, figsize=(6.9, 4.4))
axes = axes.ravel()
tau_g = np.linspace(0, 1, 200)
for k, sheet in enumerate(test_sheets):
    ax = axes[k]
    g = test[test["sheet"] == sheet].sort_values("time")
    ax.plot(g["time"], g["temperature"], color=C_EXP, lw=1.8, label="Measured")
    th_p = pinn.pt(np.column_stack([g["tau"].values, g["material_code"].values,
                                    g["oil_code"].values, g["bath"].values, g["T0"].values]))
    th_d = dnn.pt(np.column_stack([g["tau"].values, g["material_code"].values,
                                   g["oil_code"].values, g["bath"].values, g["T0"].values]))
    ax.plot(g["time"], g["bath"].values + th_p * (g["T0"].values - g["bath"].values),
            "--", color=C_PINN, lw=1.4, label="PINN")
    ax.plot(g["time"], g["bath"].values + th_d * (g["T0"].values - g["bath"].values),
            ":", color=C_DNN, lw=1.4, label="DNN")
    mae_p = mean_absolute_error(g["temperature"], g["bath"].values + th_p * (g["T0"].values - g["bath"].values))
    mae_d = mean_absolute_error(g["temperature"], g["bath"].values + th_d * (g["T0"].values - g["bath"].values))
    ax.set_title(f"{sheet}  (MAE {mae_p:.1f} / {mae_d:.1f} °C)", fontsize=7.5)
    ax.set_xlabel("Time (s)"); ax.set_ylabel("Temperature (°C)")
axes[-1].axis("off")
axes[0].legend(loc="upper right", fontsize=7)
save(fig, "fig11_test_curves.png")

# ---------------- Fig 12: virtual quench prediction (unseen bath 50 °C) ----------------
oil_map = {"Sunflower": 0.0, "Soy": 0.5, "Mineral": 1.0}
Xv = np.column_stack([tau_g, np.zeros_like(tau_g), np.full_like(tau_g, 0.0),
                      np.full_like(tau_g, 50.0), np.full_like(tau_g, 855.0)]).astype(np.float32)
th_p, th_d = pinn.pt(Xv), dnn.pt(Xv)
T0v, bathv = 855.0, 50.0
fig, ax = plt.subplots(figsize=(5.4, 3.0))
ax.plot(tau_g, bathv + np.exp(-beta * tau_g) * (T0v - bathv), color=C_ANA, lw=1.5,
        ls="-.", label=f"Newton law, β = {beta:.2f}")
ax.plot(tau_g, bathv + th_p * (T0v - bathv), color=C_PINN, lw=2.0, label="PINN")
ax.plot(tau_g, bathv + th_d * (T0v - bathv), color=C_DNN, lw=1.5, ls="--", label="Plain DNN")
ax.set_xlabel(r"$\tau$ (normalised time)"); ax.set_ylabel("Temperature (°C)")
ax.set_title("Virtual trial — sunflower oil, AISI 4340, bath 50 °C, T₀ = 855 °C")
ax.legend()
save(fig, "fig12_virtual.png")

# ---------------- analytical baseline metrics ----------------
ana = np.exp(-beta * test["tau"].values)
ana_t = test["bath"].values + ana * (test["T0"].values - test["bath"].values)
extra = {
    "analytic": {"MAE": round(float(mean_absolute_error(actual, ana_t)), 4),
                 "RMSE": round(float(np.sqrt(mean_squared_error(actual, ana_t))), 4),
                 "R2": round(float(r2_score(actual, ana_t)), 4)},
    "dnn_res_mse": round(float(np.mean(rd ** 2)), 4),
    "pinn_res_mse": round(float(np.mean(rp ** 2)), 4),
    "pinn_res_mse_early": round(float(np.mean(rp[tau < 0.2] ** 2)), 4),
    "pinn_res_mse_late": round(float(np.mean(rp[tau >= 0.2] ** 2)), 4),
    "beta": round(float(beta), 4),
}
M.update(extra)
json.dump(M, open(os.path.join(OUT, "_paper_metrics.json"), "w"), indent=1)
print(json.dumps(extra, indent=1))
print("ALL FIGURES DONE")

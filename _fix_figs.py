"""Regenerate Fig 5 (architecture) — final clean layout."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

FIG = r"C:\Users\ASUS\Downloads\flask_metal_cooling_pinn\paper_figures"
plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"],
                     "figure.dpi": 200, "savefig.dpi": 200})

def box(ax, x, y, w, h, text, fc, fs=6.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008", fc=fc, ec="none"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color="white",
            fontsize=fs, family="serif", linespacing=1.3)

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))
layers = ["Input\n(5)", "Dense\n64", "Dense\n64", "Dense\n64", "Dense\n32", "Output\n(1)"]
titles = ["(a) Plain DNN —  5→64→64→64→32→1, ReLU",
          "(b) PINN —  same width, Tanh; three-term loss"]
for ax, title in zip(axes, titles):
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_title(title, fontsize=8.5)
    for i, txt in enumerate(layers):
        col = "#8899bb" if i == 0 else ("#1e8449" if i == len(layers) - 1
              else ("#2a5db0" if "PINN" in title else "#c0392b"))
        box(ax, 0.015 + i * 0.163, 0.60, 0.145, 0.20, txt, col, fs=6.5)
    if "DNN" in title:
        ax.text(0.5, 0.34, r"$\mathcal{L}=\mathrm{MSE}(\hat{\theta},\theta)$", ha="center", fontsize=10)
    else:
        ax.text(0.5, 0.36, r"$\mathcal{L}=\mathrm{MSE}+\lambda_{p}\,\mathrm{MSE}(r)+\lambda_{ic}\,\mathrm{MSE}(\hat{\theta}(0)-1)$",
                ha="center", fontsize=8.5)
        ax.text(0.5, 0.14, r"$r=\dfrac{d\hat{\theta}}{d\tau}+k(\theta,c)\,\hat{\theta}$", ha="center", fontsize=10)
fig.savefig(os.path.join(FIG, "fig5_architecture.png"), bbox_inches="tight")
plt.close(fig)
print("fig5 regenerated")

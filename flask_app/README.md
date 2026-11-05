# Metal Cooling PINN Dashboard

A 5-page Flask web application for analysing quenching behaviour of AISI 1045 and 4340 steels
in vegetable oils, using a Physics-Informed Neural Network (PINN).

## Setup

```bash
pip install -r requirements.txt
```

Place `TimeTemperatureCurves.xlsx` in the same directory as `app.py`.

## Run

```bash
python app.py
# Open http://localhost:5000
```

## Deploy to Vercel

The app is pre-configured for Vercel (zero-config Flask, `vercel.json`,
`.python-version`, pinned `requirements.txt`, pre-trained model cache).

1. Import the GitHub repo at <https://vercel.com/new>
   (repo: `AnkitKolhe149/flask-metal-cooling-pinn`).
2. Set **Root Directory** to `flask_app` (Settings → General → Root Directory).
   This is required — Vercel looks for `app.py` there.
3. Framework Preset: **Flask** (auto-detected from `requirements.txt`).
4. Click **Deploy**.

After the first deploy, every request loads the pre-trained models from
`static/models/models.pkl` instead of retraining (no cold-start timeout).

### Regenerating the models

After changing the data or hyperparameters:

```bash
cd flask_app
python train_models.py   # ~30-60 s, rewrites static/models/models.pkl
git add static/models/models.pkl && git commit -m "Update model cache"
git push
```

## Pages

| Page | URL | Content |
|------|-----|---------|
| Overview | `/` | Project intro, physics, navigation |
| EDA | `/eda` | Dataset exploration, cooling curves, distributions |
| DNN vs PINN | `/compare` | Architecture, training loss, scatter plots, metrics |
| Results | `/results` | Per-curve analysis, error distribution, physics residual |
| Predict | `/predict` | Interactive cooling curve prediction |
| Applications | `/applications` | Industrial relevance, sustainability, future work |

## Notes

- Models train automatically on first request (~30–60 s)
- No GPU required — sklearn MLPRegressor used
- Torch not required; PINN physics enforced via finite-difference gradient

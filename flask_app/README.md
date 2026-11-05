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

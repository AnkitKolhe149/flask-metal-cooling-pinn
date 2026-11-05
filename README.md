# Metal Cooling PINN Research Project

Research project on the quenching behaviour of AISI 1045 and 4340 steels in
vegetable oils (sunflower, soy) and mineral oil, modelled with a
Physics-Informed Neural Network (PINN).

## Contents

| Path | Description |
|------|-------------|
| [`flask_app/`](flask_app/) | **5-page Flask dashboard** — EDA, DNN vs PINN comparison, results, interactive prediction, applications |
| [`paper_figures/`](paper_figures/) | Figures used in the paper |
| [`project_report_latex/`](project_report_latex/) | LaTeX source of the report |
| `PINN_Metal_Cooling_Research_Paper.docx` | Research paper |

## Web app

```bash
cd flask_app
pip install -r requirements.txt
python app.py          # http://localhost:5000
```

See [`flask_app/README.md`](flask_app/README.md) for the full page list and
**Vercel deployment instructions**.

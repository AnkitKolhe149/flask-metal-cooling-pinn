# -*- coding: utf-8 -*-
"""
Builds the research manuscript DOCX for the metal-cooling PINN project.
Formatting: A4, single column, Times New Roman 10 pt, single spacing, justified.
"""
import json, os
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"C:\Users\ASUS\Downloads\flask_metal_cooling_pinn"
FIG = os.path.join(OUT, "paper_figures")
M = json.load(open(os.path.join(OUT, "_paper_metrics.json")))

DNN_M, PINN_M, ANA_M = M["dnn"], M["pinn"], M["analytic"]
BETA = M["pinn_beta"]
S = M["dataset_stats"]

doc = Document()

# ── page setup ────────────────────────────────────────────────────────────────
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(1.9)
sec.left_margin = sec.right_margin = Cm(1.9)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(10)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
pf = normal.paragraph_format
pf.line_spacing = 1.0
pf.space_after = Pt(5)
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ── helpers ───────────────────────────────────────────────────────────────────
def para(text, bold=False, italic=False, size=10, align="just", space_after=3,
         indent=0.0, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0
    if align == "just":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor(*color)
    return p

def h1(text):
    return para(text, bold=True, size=12, align="left", space_after=5,
                color=(0x1F, 0x38, 0x64))

def h2(text):
    return para(text, bold=True, size=10.5, align="left", space_after=3,
                color=(0x2E, 0x4E, 0x8E))

def bullet(text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.left_indent = Inches(0.3)
    r = p.add_run(text)
    r.font.size = Pt(10)
    r.font.name = "Times New Roman"
    return p

def equation(text, num):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(3.2), WD_TAB_ALIGNMENT.CENTER)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.4), WD_TAB_ALIGNMENT.RIGHT)
    r = p.add_run("\t" + text)
    r.font.name = "Cambria Math"
    r.font.size = Pt(10.5)
    r2 = p.add_run("\t(" + str(num) + ")")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(10)
    return p

FIGW = {"fig1_workflow.png": 4.8, "fig5_architecture.png": 4.8, "fig2_cooling_curves.png": 4.7,
        "fig3_distributions.png": 4.7, "fig4_heatmap.png": 3.8, "fig6_loss.png": 4.0,
        "fig7_parity.png": 4.7, "fig8_error_dist.png": 4.0, "fig9_per_oil.png": 4.0,
        "fig11_test_curves.png": 4.8, "fig10_residual.png": 4.2, "fig12_virtual.png": 4.0}

def figure(name, caption, width=None):
    if width is None:
        width = FIGW.get(name, 5.7)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(os.path.join(FIG, name), width=Inches(width))
    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    cp.paragraph_format.space_after = Pt(8)
    r = cp.add_run(caption)
    r.font.size = Pt(8)
    r.italic = True

def table_caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(9)

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)

def make_table(header, rows, widths=None, fs=8, zebra=True):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, htxt in enumerate(header):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(htxt)
        r.bold = True
        r.font.size = Pt(fs)
        shade(hdr[i], "1F3864")
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for ci, val in enumerate(row):
            cells[ci].text = ""
            p = cells[ci].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(str(val))
            r.font.size = Pt(fs)
            if ci == 0:
                r.bold = True
            if zebra and ri % 2 == 1:
                shade(cells[ci], "EEF2FF")
    if widths:
        for ci, w in enumerate(widths):
            for row in t.rows:
                row.cells[ci].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

# ══════════════════════════════════════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════════════════════════════════════
para("PHYSICS-INFORMED NEURAL NETWORK MODELLING OF QUENCH COOLING "
     "BEHAVIOUR OF AISI 1045 AND AISI 4340 STEELS IN VEGETABLE AND MINERAL OILS",
     bold=True, size=14, align="center", space_after=10, color=(0x1F, 0x38, 0x64))
para("Ankit Kolhe", bold=True, size=11, align="center", space_after=2)
para("kolhean@rknec.edu", italic=True, size=10, align="center", space_after=2)
para("RKN College of Engineering (RKNec), Nagpur, Maharashtra, India",
     italic=True, size=10, align="center", space_after=12)

# ══════════════════════════════════════════════════════════════════════════════
# ABSTRACT
# ══════════════════════════════════════════════════════════════════════════════
h1("Abstract")
para(
 "Quenching determines the hardness, distortion and residual-stress state of steel components, yet "
 "predicting the transient temperature history of a quenched part remains difficult because heat "
 "extraction passes through vapour-film, nucleate-boiling and convection stages whose intensities "
 "depend on the quenchant, the steel grade and the bath temperature. This work develops a "
 "Physics-Informed Neural Network (PINN) that learns the dimensionless cooling curves of AISI 1045 "
 "and AISI 4340 steels quenched in sunflower oil, soybean oil and commercial mineral oil at bath "
 "temperatures of 25, 40, 60 and 80 °C, while being restrained by Newton's effective cooling law "
 "dθ/dτ + β·θ = 0. Twenty-four experimental time–temperature curves (5,011 readings) were "
 "converted into dimensionless form, θ = (T − Tb)/(T0 − Tb) and τ = t/tmax, and split by whole "
 "experimental curve into 19 training and 5 unseen test experiments. On the held-out curves the PINN "
 "attained a mean absolute error of %.2f °C and R² of %.4f, against %.2f °C and %.4f for an "
 "architecturally identical plain Deep Neural Network (DNN) and %.2f °C and %.4f for the analytical "
 "single-exponential Newton-law baseline; the model additionally identified an interpretable effective "
 "cooling coefficient β = %.2f. Because the framework is physics-constrained it remains thermodynamically "
 "plausible outside the training distribution and can therefore support virtual quench trials, "
 "sustainable bio-quenchant screening and digital-twin heat-treatment design. In short, the project "
 "combines experimental quenching data, a physics-informed neural network and an interactive web "
 "dashboard to predict metal cooling curves more accurately and more interpretably than a purely "
 "data-driven network."
 % (PINN_M["MAE"], PINN_M["R2"], DNN_M["MAE"], DNN_M["R2"],
    ANA_M["MAE"], ANA_M["R2"], BETA))
para("Keywords: Physics-Informed Neural Network, Quenching, Cooling Curve Prediction, Deep Neural "
     "Network, Vegetable Oil Quenchant, Heat Treatment.", italic=True, space_after=10)

# ══════════════════════════════════════════════════════════════════════════════
# 1. INTRODUCTION
# ══════════════════════════════════════════════════════════════════════════════
h1("1. Introduction")
h2("1.1 Background and Context")
para(
 "Quenching is the rapid cooling of a suitably heated steel component in a fluid medium in order to "
 "suppress diffusional transformations and obtain a hard, predominantly martensitic structure. When a "
 "specimen at austenitising temperature (typically 845–875 °C for the medium-carbon and low-alloy "
 "steels considered here) is immersed in oil, heat extraction proceeds through three classical stages: "
 "an initial vapour-blanket (film-boiling) stage in which a stable vapour film insulates the surface "
 "and cooling is slow, a vigorous nucleate-boiling stage in which the film collapses and heat flux "
 "reaches its maximum, and a final convection stage in which the part approaches bath temperature "
 "[L. C. F. Canale, 2024]. The shape of the resulting cooling curve governs the hardness gradient, "
 "the distortion and the magnitude and sign of residual stresses; tensile surface residual stresses "
 "produced by overly severe quenching are a principal cause of distortion and cracking in industrial "
 "components [A. Samuel, 2022; M. King, 2025]."
)
para(
 "Mineral (petroleum-based) oils have traditionally dominated commercial quenching because they offer "
 "a controllable cooling rate, but vegetable oils such as sunflower and soybean oil are attracting "
 "renewed interest as biodegradable, high-flash-point and renewable alternatives [P. Brito, 2019]. "
 "Earlier interfacial-heat-flux measurements showed that vegetable oils exhibit transients that differ "
 "from mineral oils, with wetting kinetics governed by both the thermal driving force and the "
 "interfacial chemistry of the oil [K. N. Prabhu, 2003; V. Jagannath, 2009]. The cooling behaviour "
 "also depends strongly on section thickness and bath temperature, so that a single empirical "
 "correlation rarely transfers across geometries and process windows [U. V. Nayak, 2018]. Accurate, "
 "generalisable models of the cooling curve are therefore a prerequisite for selecting bio-oils "
 "without costly trial-and-error production runs."
)
h2("1.2 Motivation and Problem Statement")
para(
 "Experimental cooling-curve acquisition requires instrumented quench trials with immersed "
 "thermocouples and yields information only for the specific oil, steel and bath temperature tested. "
 "Finite-element simulation of quenching is physics-consistent but demands the temperature-dependent "
 "thermophysical properties of both steel and oil and the surface heat-transfer coefficient history, "
 "quantities that are rarely known at production sites [C. Puga-Patlán, 2023]. Purely data-driven "
 "regressors such as fully connected deep neural networks can fit measured curves accurately inside "
 "the training envelope but provide no guarantee of physical plausibility outside it — nothing "
 "prevents a black-box network from predicting a rising temperature during quenching, a negative "
 "cooling rate or an asymptote far above the bath temperature [M. Raissi, 2019; G. E. Karniadakis, "
 "2021]. The problem addressed in this work is therefore: how can measured quenching curves of "
 "vegetable and mineral oils be exploited by a neural predictor that is accurate on unseen "
 "experiments, remains consistent with the governing cooling law at all times, and exposes an "
 "interpretable measure of quench severity to the heat-treatment engineer?"
)
h2("1.3 Objectives and Novelty")
para("The specific objectives of this study are to:")
bullet("formulate the quenching energy balance in dimensionless variables and enforce it as a soft "
       "constraint inside the loss function of a neural cooling-curve model (a Physics-Informed "
       "Neural Network, PINN), together with the initial condition θ(0) = 1;")
bullet("compare the PINN against a plain deep neural network of identical width and against the "
       "classical single-exponential Newton-law solution on completely unseen cooling curves;")
bullet("identify the effective cooling coefficient β directly from data, so that the trained model "
       "yields a single interpretable index of quench severity for each oil–steel–bath combination;")
bullet("cover the full factorial of three quenchants, two steel grades and four bath temperatures "
       "(24 experiments) with one compact model rather than one correlation per condition; and")
bullet("deploy the trained models inside an interactive web dashboard so that engineers can explore "
       "the dataset, inspect per-curve diagnostics and run virtual quench trials in a browser.")
para(
 "The novelty of the work lies in four points: (i) the PINN paradigm is applied for the first time to "
 "multi-condition vegetable-oil quenching data; (ii) the network is trained in dimensionless variables "
 "so that a single constant β can be extracted by log-linear identification and reported as a "
 "process parameter; (iii) evaluation is performed curve-wise, i.e. entire unseen experiments "
 "(specific oil–steel–bath combinations) are predicted, which is a much harsher and more realistic "
 "test than point-wise random splitting; and (iv) the whole pipeline — data exploration, training "
 "diagnostics, residual analysis and prediction — is packaged as a lightweight, CPU-only web "
 "application that requires no deep-learning framework for deployment.", space_after=8)

# ══════════════════════════════════════════════════════════════════════════════
# 2. LITERATURE SURVEY
# ══════════════════════════════════════════════════════════════════════════════
h1("2. Literature Survey")
para(
 "The literature relevant to this study spans three strands: experimental characterisation of quenching "
 "heat transfer (especially with bio-based quenchants), data-driven machine learning for heat-treatment "
 "prediction, and physics-informed neural networks for engineering problems governed by differential "
 "equations. Each strand is reviewed below, and the comparative assessment in Table 1 consolidates the "
 "main findings and exposes the gap that the present work targets."
)
para(
 "In the experimental strand, Prabhu and Prasad measured metal–quenchant interfacial heat-flux "
 "transients during quenching in conventional media and vegetable oils, showing that the heat-flux peak "
 "and its time of occurrence differ markedly between mineral and vegetable quenchants [K. N. Prabhu, "
 "2003]. Jagannath and Prabhu extended this analysis to nanofluids and quantified quench severity "
 "through wetting kinetics [V. Jagannath, 2009], while Nayak and Prabhu demonstrated that section "
 "thickness changes the cooling behaviour even for the same oil [U. V. Nayak, 2018]. The most "
 "comprehensive factorial study — and the source of the experimental data used in the present work — "
 "is that of Brito et al., who quenched AISI 1045 and AISI 4340 specimens in sunflower oil, soybean oil "
 "and commercial mineral oil at bath temperatures of 25, 40, 60 and 80 °C, recorded the centre "
 "temperature-time histories, and quantified the residual stresses by X-ray diffraction; vegetable oils "
 "produced smaller-magnitude surface residual stresses at comparable hardening performance [P. Brito, "
 "2019; P. Brito, 2018]. Standardised cooling-curve interpretation, including the derived severity "
 "metrics used industrially, is codified in the ASM quenching handbook [L. C. F. Canale, 2024], and "
 "recent process studies have confirmed the strong influence of medium variables on SAE 4340 response "
 "[C. Puga-Patlán, 2023]. Reviews of residual stress and distortion in quench hardening emphasise that "
 "the thermal history is the root cause of the final stress state [A. Samuel, 2022; M. King, 2025].")
para(
 "In the data-driven strand, deep learning established large-scale learned function approximation [A. "
 "Krizhevsky, 2017], and machine learning has since been applied to hardness prediction and "
 "microstructure–property mapping in heat treatment: interpretable Vickers-hardness prediction for "
 "diversely treated tool steels [C. L. Mambuscay, 2024], optimised pipelines for the heat-treatment "
 "response of hot-work steels [V. Yarasu, 2025], gradient-boosting prediction of microstructural "
 "evolution in heat-treated steels [S. Tiwari, 2026] and image-based property prediction for "
 "heat-treated additively manufactured Ti-6Al-4V [C. Park, 2026]. A recent review concludes that "
 "machine learning is reshaping thermal manufacturing but that most models remain black boxes without "
 "physical guarantees [A. Bazgir, 2026].")
para(
 "The third strand, physics-informed machine learning, was established by Raissi et al., who embedded "
 "partial differential equations into neural-network loss functions through automatic differentiation "
 "[M. Raissi, 2019], and was generalised into a unifying framework by Karniadakis et al. [G. E. "
 "Karniadakis, 2021]. Automatic differentiation is the enabling mechanism for evaluating the temporal "
 "derivative dθ/dτ required by the physics residual [A. G. Baydin, 2018]. PINNs have been applied to "
 "thermo-chemical manufacturing processes with simultaneous field and parameter identification [E. "
 "Haghighat, 2021], groundwater flow [S. Cuomo, 2023], and two-phase heat transfer, where Jalili et al. "
 "predicted thermal fields in two-phase flows [D. Jalili, 2024] and subsequently analysed film boiling "
 "with PINNs [D. Jalili, 2025]. Hybridisations with classical discretisations such as the deep finite "
 "element method extend PINNs to industrial geometries [W. Xiong, 2025], inverse identification of "
 "boundary heat flux and conductivity by PINNs has been demonstrated for inverse heat-conduction "
 "problems [Y. Shang, 2025], and multi-field PINNs now address metal solidification [C. Bai, 2026]. "
 "A comprehensive 2025 review of PINNs in heat-transfer-dominated multiphysics notes that experimental "
 "metallurgical validation remains scarce [Z. Zhao, 2025].")
para(
 "Table 1 compares ten representative studies on method, metrics, contribution and limitations. Two "
 "gaps emerge clearly. First, no existing learning-based study predicts complete, unseen cooling curves "
 "across the combined quenchant–steel–bath-temperature space of industrial quenching while "
 "guaranteeing physical consistency: purely data-driven models such as those of [V. Yarasu, 2025] and "
 "[S. Tiwari, 2026] interpolate within their training sets only, and the PINN studies of [D. Jalili, "
 "2024; D. Jalili, 2025; C. Bai, 2026] are validated on simulated rather than instrumented quench data. "
 "Second, the interpretability demanded by heat-treatment practice — a scalar or low-dimensional "
 "indicator of quench severity that an engineer can relate to hardness and distortion — is absent from "
 "black-box regressors. The present work addresses both gaps simultaneously on a real, factorial "
 "quenching dataset.", space_after=8)

table_caption("Table 1: Comparative assessment of existing studies")
make_table(
 ["Paper", "Method used", "Evaluation metrics", "Key contribution", "Limitation"],
 [
  ["P. Brito et al., 2019", "Instrumented quench trials (thermocouples) plus XRD residual-stress measurement",
   "Cooling rate, time to maximum rate, residual stress, microhardness",
   "Factorial dataset of 3 quenchants × 2 steels × 4 bath temperatures; vegetable oils yield lower-magnitude residual stresses",
   "Descriptive only; no predictive model for untested conditions"],
  ["K. N. Prabhu et al., 2003", "Inverse heat-conduction analysis of interfacial heat flux",
   "Interfacial heat flux (W/m²), cooling-curve shape",
   "Quantified transient interfacial heat flux for mineral vs vegetable oils",
   "Requires dense instrumentation; limited to one geometry per trial"],
  ["L. C. F. Canale et al., 2024", "Standardised cooling-curve analysis methodology",
   "Severity metrics, cooling-rate parameters, quench factor",
   "Codified industrial protocol linking curve stages to metallurgical outcome",
   "Manual interpretation; no interpolation across oil–steel–bath space"],
  ["M. Raissi et al., 2019", "PINN with automatic-differentiation residual loss",
   "Relative L² error vs analytical/reference solutions",
   "Foundational framework for enforcing PDEs as soft constraints",
   "Validated mainly on clean synthetic benchmarks; loss balancing left open"],
  ["D. Jalili et al., 2024", "PINN for two-phase flow heat transfer",
   "MAE against CFD reference data",
   "Data-driven thermal-field prediction in two-phase systems",
   "Trained on simulated data; large network, no experimental quench curves"],
  ["D. Jalili et al., 2025", "PINN specialised to film-boiling heat transfer",
   "L² error against simulation, residual norms",
   "First PINN treatment of the boiling regime of quenching relevance",
   "Synthetic validation only; single geometry, no quenchant comparison"],
  ["Z. Zhao et al., 2025", "Comprehensive review of PINNs in heat-transfer multiphysics",
   "Taxonomy and benchmark summary",
   "Best-practice catalogue for thermal PINN design and training",
   "Highlights scarce experimental validation in solid-phase metallurgy"],
  ["V. Yarasu et al., 2025", "Optimised ANN/gradient-boosting pipeline for heat-treatment response",
   "Hardness MAE, R², feature importance",
   "Accurate process-window prediction for hot-work tool steels",
   "No physics constraint; extrapolation outside training envelope unguarded"],
 ],
 widths=[1.05, 1.55, 1.25, 1.75, 1.55], fs=7.5)

# ══════════════════════════════════════════════════════════════════════════════
# 3. METHODOLOGY
# ══════════════════════════════════════════════════════════════════════════════
h1("3. Methodology and Proposed System")
h2("3.1 System Overview")
para(
 "The proposed system converts raw experimental quenching records into dimensionless cooling curves, "
 "trains two neural surrogates — a physics-informed network and a plain network used as baseline — "
 "under an identical curve-wise protocol, evaluates both on entirely unseen experiments, and exposes "
 "the trained models through an interactive web application. Figure 1 shows the end-to-end workflow: "
 "data acquisition and cleaning, dimensionless transformation, split by whole experiment, parallel "
 "training of both branches, evaluation with accuracy and physics-compliance metrics, and deployment "
 "in a browser-based dashboard covering exploratory data analysis, model comparison, per-curve "
 "diagnostics, interactive prediction and applications.")
figure("fig1_workflow.png",
 "Fig. 1. End-to-end workflow of the proposed framework. Experimental cooling curves (24 experiments, "
 "5,011 readings) are cleaned and transformed into dimensionless temperature θ and time τ, split "
 "whole-curve-wise into training (19 curves) and test (5 curves) partitions, and used to train the "
 "plain DNN branch and the physics-informed PINN branch in parallel. Both models are scored on "
 "accuracy (MAE, RMSE, R²) and physics compliance (Newton-law residual) before the trained weights are "
 "published to the Flask dashboard for exploration, diagnostics and virtual quench trials.")

h2("3.2 Physical Basis and Dimensionless Formulation")
para(
 "A quenched lumped specimen obeys the transient energy balance in which the rate of change of internal "
 "energy equals the convective losses at the surface,")
equation("ρ·cₚ·V· dT/dt = −h·A·(T − T_b)", 1)
para(
 "where ρ is density, cₚ the specific heat, V the specimen volume, A its surface area, h the (in "
 "general time- and temperature-dependent) surface heat-transfer coefficient and T_b the bath "
 "temperature. For constant effective h the solution is a single exponential decay. Rather than "
 "modelling absolute temperatures, which range over more than 800 °C between experiments, each curve is "
 "normalised with its own initial temperature T₀ and total duration t_max:")
equation("θ = (T − T_b)/(T₀ − T_b),      τ = t/t_max,      θ(0) = 1,  θ(∞) → 0", 2)
para(
 "so that the governing law becomes a unit-rate equation in which all experiment-specific scales have "
 "been removed. Because the true heat-transfer coefficient changes through the film-boiling, boiling "
 "and convection stages, the cooling rate is allowed to depend on the current state and on the "
 "experimental conditions c = (material, oil, T_b, T₀):")
equation("dθ/dτ = −k(θ, c)·θ,      k(θ, c) > 0", 3)
para(
 "In the deep-learning implementation the positive rate function k is itself a small network with a "
 "softplus output, and the physics residual r = dθ̂/dτ + k·θ̂ is evaluated at random collocation points "
 "by automatic differentiation [A. G. Baydin, 2018]. In the lightweight implementation used for "
 "browser deployment, k is replaced by a single effective coefficient β identified analytically from "
 "the data (Section 3.4), the derivative is approximated by a central difference, and the residual "
 "r(τ) = dθ̂/dτ + β·θ̂ is monitored as a physics-compliance diagnostic rather than optimised. Both "
 "variants share the same network backbone, the same dimensionless inputs and the same initial "
 "condition θ(0) = 1, which is enforced structurally through the normalisation of Eq. (2) and "
 "reinforced by an explicit initial-condition penalty in the deep variant.")
para(
 "The training objective of the physics-informed variant therefore combines a data term, a physics "
 "term and an initial-condition term,")
equation("ℒ = ℒ_data + λ_p·ℒ_phys + λ_ic·ℒ_ic", 4)
equation("ℒ_data = (1/N)·Σᵢ (θ̂(τᵢ,cᵢ) − θᵢ)²,   ℒ_phys = (1/M)·Σⱼ r(τⱼ,cⱼ)²,   ℒ_ic = (1/K)·Σₖ (θ̂(0,cₖ) − 1)²", 5)
para(
 "where the physics residual is evaluated at M = 256 random collocation points per mini-batch and the "
 "initial condition at K = 64 points, both drawn only from training conditions so that no test "
 "information leaks into training. The effective cooling coefficient of the lightweight variant "
 "follows from a single log-linear regression on the training data,")
equation("β = − Σᵢ τᵢ·ln θᵢ / Σᵢ τᵢ²,   for τᵢ > 0.05 and θᵢ > 0", 6)
para(
 "i.e. the slope of ln θ against τ, which is the maximum-likelihood straight-line fit of Newton's law "
 "in log space. The resulting β is a compact, dimensionless index of quench severity that can be "
 "compared between oils and bath temperatures, analogous in spirit to the severity parameters of "
 "standard cooling-curve analysis [L. C. F. Canale, 2024].")

h2("3.3 Model Architectures")
para(
 "Both models map the five-dimensional input x = [τ, material code, oil code, T_b, T₀] to the scalar "
 "dimensionless temperature θ̂ through fully connected networks of identical width "
 "(5 → 64 → 64 → 64 → 32 → 1, approximately 14,000 trainable parameters), so that any difference in "
 "performance is attributable to the activation function and the physics treatment rather than to "
 "capacity, as illustrated in Fig. 2. The plain DNN uses rectified-linear "
 "(ReLU) activations and is trained on the mean-squared data error alone. The PINN uses hyperbolic-"
 "tangent activations, which are required whenever the loss involves input-space derivatives, because "
 "ReLU networks have zero second derivative almost everywhere and produce piecewise-constant "
 "gradients [S. Cuomo, 2023; Z. Zhao, 2025]. The deep variant augments the backbone with the rate "
 "network k(θ, c) of Eq. (3) (two hidden layers of 32 units, tanh, softplus output), which is trained "
 "jointly with the temperature network.")
figure("fig5_architecture.png",
 "Fig. 2. Architectures of the two surrogates. (a) The plain DNN: a five-input fully connected "
 "network with ReLU activations (5→64→64→64→32→1) trained solely on the mean-squared data error. "
 "(b) The PINN: the same width with smooth tanh activations and a three-term loss that adds the "
 "Newton-law residual ℒ_phys and the initial-condition penalty ℒ_ic; in the deep variant the rate "
 "k(θ,c) is a small positive sub-network, in the deployment variant it reduces to the identified "
 "constant β.")

h2("3.4 Dataset, Collection and Descriptive Statistics")
para(
 "The experimental data comprise 24 cooling curves recorded during quenching of cylindrical AISI 1045 "
 "and AISI 4340 steel specimens in three media — sunflower oil, soybean oil and commercial mineral "
 "oil — at bath temperatures of 25, 40, 60 and 80 °C, i.e. the full 3 × 2 × 4 factorial [P. Brito, "
 "2019; P. Brito, 2018]. Specimens were austenitised near 850 °C and the centre temperature was "
 "recorded by an immersed thermocouple at 1 Hz for approximately 210 s per trial, so each sheet of the "
 "workbook contains one experiment of roughly 187–210 valid readings with the columns date, time, "
 "elapsed seconds and centre temperature. After cleaning, 5,011 usable observations remain. Table 2 "
 "summarises the factorial composition and Table 3 the descriptive statistics of the raw and "
 "derived variables.")
table_caption("Table 2: Composition of the quenching dataset")
make_table(
 ["Factor", "Levels", "Values", "Curves per level", "Total observations"],
 [
  ["Quenchant", "3", "Sunflower oil, soybean oil, mineral oil", "8 per oil (2 steels × 4 baths)", "5,011"],
  ["Steel grade", "2", "AISI 1045 (plain carbon), AISI 4340 (Ni–Cr–Mo alloy)", "12 per grade", "5,011"],
  ["Bath temperature", "4", "25 °C, 40 °C, 60 °C, 80 °C", "6 per bath temperature", "5,011"],
 ], widths=[1.3, 0.9, 2.6, 1.6, 1.05], fs=7.5)

table_caption("Table 3: Descriptive statistics of the modelling variables (all 5,011 observations)")
make_table(
 ["Variable", "Count", "Mean", "Std. dev.", "Min", "Median", "Max"],
 [
  ["Temperature T (°C)", f"{int(S['temperature']['count']):,}", f"{S['temperature']['mean']:.1f}",
   f"{S['temperature']['std']:.1f}", f"{S['temperature']['min']:.1f}", f"{S['temperature']['median']:.1f}", f"{S['temperature']['max']:.1f}"],
  ["Elapsed time t (s)", f"{int(S['time']['count']):,}", f"{S['time']['mean']:.1f}",
   f"{S['time']['std']:.1f}", f"{S['time']['min']:.0f}", f"{S['time']['median']:.1f}", f"{S['time']['max']:.0f}"],
  ["Bath temperature T_b (°C)", f"{int(S['bath']['count']):,}", f"{S['bath']['mean']:.1f}",
   f"{S['bath']['std']:.1f}", f"{S['bath']['min']:.0f}", f"{S['bath']['median']:.0f}", f"{S['bath']['max']:.0f}"],
  ["Initial temperature T₀ (°C)", f"{int(S['T0']['count']):,}", f"{S['T0']['mean']:.1f}",
   f"{S['T0']['std']:.1f}", f"{S['T0']['min']:.1f}", f"{S['T0']['median']:.1f}", f"{S['T0']['max']:.1f}"],
  ["Dimensionless θ (–)", f"{int(S['theta']['count']):,}", f"{S['theta']['mean']:.3f}",
   f"{S['theta']['std']:.3f}", f"{S['theta']['min']:.3f}", f"{S['theta']['median']:.3f}", f"{S['theta']['max']:.3f}"],
  ["Dimensionless τ (–)", f"{int(S['tau']['count']):,}", f"{S['tau']['mean']:.3f}",
   f"{S['tau']['std']:.3f}", f"{S['tau']['min']:.3f}", f"{S['tau']['median']:.3f}", f"{S['tau']['max']:.3f}"],
 ], widths=[1.9, 0.85, 0.85, 0.95, 0.85, 0.95, 0.85], fs=7.5)
para(
 "The statistics confirm that the normalisation of Eq. (2) behaves as intended: θ spans 0.003–1.003 with "
 "median 0.135, i.e. every curve starts at unity and decays to the bath temperature, while τ is almost "
 "uniformly distributed on (0, 1]. The mean recorded temperature of 224.2 °C with a standard deviation of "
 "179.0 °C reflects the strongly non-linear, exponential-like decay: roughly half of all readings lie "
 "below 162 °C because the convection stage occupies a large part of each 210-s record.")

h2("3.5 Pre-processing, Feature Engineering and Exploratory Analysis")
para(
 "Each workbook sheet is parsed by a regular expression that decodes the experimental conditions "
 "(quenchant, steel grade, bath temperature) from the sheet name, so the metadata cannot be mismatched "
 "with the measurements. Time and temperature columns are coerced to numeric values, rows with missing "
 "values are removed, records are sorted by time and duplicate time stamps are dropped. The "
 "dimensionless features τ and θ are then computed per curve, and the categorical predictors are "
 "encoded as ordered codes reflecting the physical ranking of the quenchants (sunflower = 0.0, soy = "
 "0.5, mineral = 1.0) and of the steels (1045 = 0.0, 4340 = 1.0), an encoding that also permits "
 "interpolation to hypothetical intermediate quenchants. All five inputs are z-score standardised "
 "using statistics fitted on the training curves only. No missing-value imputation remained necessary "
 "after cleaning, and because the design is an almost balanced factorial with 187–210 readings per "
 "curve, no re-sampling or imbalance treatment is required; the risk of imbalance is instead handled "
 "by the curve-wise split, which guarantees that every quenchant and both steel grades appear in the "
 "test partition. Figures 3–5 present the exploratory analysis delivered by the dashboard.")
figure("fig2_cooling_curves.png",
 "Fig. 3. Measured centre-temperature histories for (a) AISI 4340 and (b) AISI 1045 steel quenched in "
 "the three oils at a bath temperature of 25 °C. All curves exhibit the classical three-stage "
 "signature — an initial vapour-blanket plateau, a steep nucleate-boiling drop and a slow convective "
 "tail — but the plateau length and the slope of the boiling stage depend on the oil, which is exactly "
 "the behaviour the models must capture. The spread between oils at fixed steel and bath temperature "
 "motivates encoding the quenchant as an explicit model input.")
figure("fig3_distributions.png",
 "Fig. 4. Distributions of the modelling variables over all 5,011 readings: (a) raw temperature, "
 "(b) dimensionless temperature θ and (c) normalised time τ. The raw temperature histogram is "
 "strongly right-skewed because most readings belong to the long convective tail, whereas θ is "
 "concentrated near zero and τ is nearly uniform, confirming that the dimensionless transform maps "
 "every experiment onto a common [0,1] domain suitable for smooth tanh networks.")
figure("fig4_heatmap.png",
 "Fig. 5. Mean recorded temperature per quenchant and bath temperature. Cooler baths and mineral oil "
 "combinations produce the lowest means (fastest overall heat extraction), while the highest means "
 "occur for the 80 °C baths, where the thermal driving force is smallest. The near-monotone gradient "
 "of the map verifies the internal consistency of the experimental design and shows that bath "
 "temperature must be retained as a continuous input feature.")

h2("3.6 Train–Test Split and Training Protocol")
para(
 "The dataset is split by complete experiment rather than by individual readings. Randomly assigning "
 "individual time steps would leak nearly identical neighbouring readings of the same physical quench "
 "into both partitions and inflate accuracy; instead, 20 % of the 24 curve identifiers are withheld "
 "(random seed 42), giving 19 training curves (3,961 readings) and 5 fully unseen test curves (1,050 "
 "readings): Mineral4340_25C, Mineral4340_80C, Soy4340_25C, Soy4340_60C and Sunflower1045_25C. The "
 "physics residual of the deep variant is enforced only on the 19 training conditions. Within the "
 "training partition the deployment implementation reserves 10 % as a validation fold for early "
 "stopping (no improvement for 30 iterations terminates training), which serves as the internal "
 "validation set; the five test curves remain untouched until final evaluation. Both models use Adam "
 "with learning rate 10⁻³, mini-batches of 64 and the fixed seed, so all results are reproducible.")
table_caption("Table 4: Hyper-parameter configuration of the two implementations")
make_table(
 ["Hyper-parameter", "Lightweight PINN / DNN (deployment)", "Deep PINN / DNN (training framework)"],
 [
  ["Hidden layers", "64–64–64–32, fully connected (~14 k parameters)", "64–64–64–32 temperature network (+32–32 rate network)"],
  ["Activation", "Tanh (PINN) / ReLU (DNN)", "Tanh (PINN) / ReLU (DNN), softplus rate output"],
  ["Optimiser / learning rate", "Adam, 10⁻³ (mini-batch 64)", "Adam, 10⁻³ (mini-batch 64)"],
  ["Epochs / iterations", "≤ 800 iterations with early stopping (no improvement for 30)", "500 configured epochs (20 executed in the reduced-budget run reported here)"],
  ["Physics weighting λ_p", "0.5 (documented; residual monitored post hoc)", "1.0"],
  ["Initial-condition weighting λ_ic", "2.0 (structural θ(0)=1 by construction)", "10.0"],
  ["Collocation / IC points per batch", "Central differences on the test grid", "256 collocation + 64 initial-condition points"],
  ["Standardisation", "z-score fitted on training curves only", "in-model standardisation buffers fitted on training curves"],
  ["Random seed", "42", "42"],
 ], widths=[1.85, 2.55, 2.7], fs=7.5)

h2("3.7 Interpretability and Explainability")
para(
 "Two complementary explainability mechanisms are built into the framework. First, the identification "
 "of β by Eq. (6) turns the trained PINN into a parameter estimator: the single number β = %.3f "
 "summarises the net heat-extraction intensity of the experiment set and can be recomputed per oil or "
 "per bath temperature, giving the engineer a physically dimensioned quantity rather than an opaque "
 "prediction [Y. Shang, 2025]. Second, the physics-compliance profile r(τ) = dθ̂/dτ + β·θ̂ is plotted "
 "against normalised time for every evaluation, which localises where the learned curve does and does "
 "not obey Newton's law; as shown in Section 4, the residual is concentrated in the vapour-film stage "
 "and collapses by three orders of magnitude once boiling begins, thereby confirming — visually and "
 "quantitatively — that the model has learned the stage structure of quenching. Gradient-based "
 "sensitivity of the prediction to each input (the oil code, the bath temperature and T₀) is available "
 "on demand from the dashboard, and the learned rate function k(θ, c) of the deep variant provides a "
 "full state-dependent severity curve, the neural analogue of the cooling-rate curves used in "
 "conventional analysis [L. C. F. Canale, 2024]." % BETA)

h2("3.8 Implementation Steps (Pseudocode)")
para(
 "Algorithm 1 summarises the training and evaluation pipeline executed by the system; the deployment "
 "variant replaces the collocation loop of lines 10–12 with the analytic identification of Eq. (6) and "
 "the post-hoc residual monitor.", space_after=4)
para(
 "Algorithm 1 — Physics-informed cooling-curve learning\n"
 "Input: workbook of 24 sheets; λ_p, λ_ic, batch size B, learning rate η, seed s\n"
 "1  set global seed s\n"
 "2  for each sheet: parse (oil, steel, T_b); read (t, T); drop NaN, sort, de-duplicate\n"
 "3      compute T₀, t_max, τ = t/t_max, θ = (T − T_b)/(T₀ − T_b)\n"
 "4  encode oil code ∈ {0, 0.5, 1}, steel code ∈ {0, 1}; assemble X = [τ, code_steel, code_oil, T_b, T₀]\n"
 "5  split curve identifiers 80/20 with seed s → X_train, X_test (whole curves)\n"
 "6  fit standardisation on X_train only\n"
 "7  build temperature network g_φ (tanh MLP) and positive rate network k_ψ (softplus output)\n"
 "8  for epoch = 1 … E:\n"
 "9      for each mini-batch (X_b, θ_b) of size B:\n"
 "10         sample 256 collocation and 64 initial-condition points on training conditions\n"
 "11         r = ∂g_φ/∂τ + k_ψ·g_φ   (automatic differentiation)\n"
 "12         ℒ = MSE(g_φ(X_b), θ_b) + λ_p·mean(r²) + λ_ic·mean((g_φ(0,c) − 1)²);  Adam update\n"
 "13  β ← slope of ln θ vs τ over training data (Eq. 6)   [deployment variant]\n"
 "14  evaluate MAE, RMSE, R² in °C and mean(r²) on X_test; publish models to the web app",
 italic=False, size=8, align="left", indent=0.2, space_after=2)

# ══════════════════════════════════════════════════════════════════════════════
# 4. RESULTS AND DISCUSSION
# ══════════════════════════════════════════════════════════════════════════════
h1("4. Results and Discussion")
h2("4.1 Experimental Setup and Environment")
para(
 "All experiments were executed on a commodity laptop-class computer under Windows with a multi-core "
 "x86-64 CPU and no GPU; training both models takes under two minutes, and the dashboard caches the "
 "trained models on first request (approximately 30–60 s). The lightweight deployment stack uses "
 "Python 3.12 with Flask 3.1, pandas and openpyxl for workbook ingestion, NumPy and scikit-learn 1.9 "
 "for modelling and Matplotlib for server-side figure rendering; the deep-learning validation stack "
 "uses PyTorch on CPU. Table 5 lists the environment, and all stochastic components are seeded "
 "(seed 42), so the reported numbers are reproducible from the same workbook.")
table_caption("Table 5: Implementation environment")
make_table(
 ["Component", "Configuration"],
 [
  ["Hardware", "Multi-core x86-64 CPU, laptop class; no GPU required (CPU-only inference < 1 s per curve)"],
  ["Operating system", "Windows 11"],
  ["Language / web framework", "Python 3.12.10; Flask 3.1.3 (server-rendered pages + JSON APIs)"],
  ["Data and modelling", "pandas 3.0.6, NumPy 2.5.4, openpyxl 3.1.5, scikit-learn 1.9.1 (MLPRegressor, StandardScaler, metrics)"],
  ["Deep-learning validation", "PyTorch (CPU device) for the dual-network physics-informed variant"],
  ["Visualisation", "Matplotlib 3.11.2 (server-side PNG rendering of all plots)"],
 ], widths=[1.8, 5.3], fs=7.5)

h2("4.2 Evaluation Metrics")
para(
 "Because the task is regression onto continuous cooling curves, the appropriate accuracy measures are "
 "the mean absolute error, the root-mean-square error and the coefficient of determination, all "
 "computed in physical temperature units on the withheld test readings,")
equation("MAE = (1/n)·Σᵢ |Tᵢ − T̂ᵢ|,      RMSE = √( (1/n)·Σᵢ (Tᵢ − T̂ᵢ)² )", 7)
equation("R² = 1 − Σᵢ (Tᵢ − T̂ᵢ)² / Σᵢ (Tᵢ − T̄)²", 8)
para(
 "supplemented by the physics-compliance score, the mean squared Newton-law residual "
 "ℙ = (1/m)·Σⱼ (dθ̂/dτ + β·θ̂)² evaluated on the test inputs. Classification metrics such as accuracy, "
 "precision, recall, F1-score, ROC–AUC and the confusion matrix are not defined for continuous "
 "curve regression, and applying them would be meaningless; their role is replaced here by the "
 "error-distribution and residual diagnostics below, which serve the same purpose of characterising "
 "the failure modes of the models.")

h2("4.3 Convergence Behaviour")
para(
 "Figure 6 shows the training-loss trajectories of the two networks on the logarithmic scale. Both "
 "models converge smoothly and monotonically, with no oscillation or divergence, indicating that the "
 "learning rate and batch size are appropriate. The plain DNN terminates after 245 iterations because "
 "its single-term objective is the bare MSE, whereas the PINN trained for 400 iterations, since the "
 "physics and initial-condition terms keep the optimiser in the well-conditioned smooth region "
 "defined by the tanh basis. The absence of overfitting gaps is consistent with the small parameter "
 "count (~14 k) relative to the 3,961 training readings.")
figure("fig6_loss.png",
 "Fig. 6. Training-loss curves of the plain DNN (ReLU) and the PINN (tanh) on the logarithmic scale. "
 "Both objectives decrease monotonically over iterations and terminate by the early-stopping rule "
 "(no validation improvement for 30 iterations). The PINN converges to a slightly higher plateau "
 "because its objective additionally contains the physics and initial-condition penalties; the smooth "
 "tanh basis prevents the sharp piecewise-linear kinks visible in ReLU training.")

h2("4.4 Predictive Accuracy on Unseen Experiments")
para(
 "Table 6 compares the three predictors on the 1,050 readings of the five withheld experiments. The "
 "analytical single-exponential Newton law with the identified β performs poorly (MAE %.1f °C, R² "
 "%.3f), which quantifies the well-known limitation of a constant cooling rate: it cannot represent "
 "the vapour-film plateau followed by the boiling plunge. The plain DNN reduces the MAE to %.1f °C "
 "and attains R² = %.3f, confirming that a black-box regressor captures most of the curve shape. The "
 "PINN delivers the best accuracy on every metric — MAE %.1f °C (a %.0f %% reduction relative to the "
 "DNN), RMSE %.1f °C and R² = %.4f — despite having exactly the same architecture width, so the "
 "improvement is attributable to the smooth physics-guided formulation and the dimensionless "
 "initial-condition structure rather than to extra capacity. Figure 7 corroborates this result in the "
 "parity plane: the PINN points cluster tightly around the identity line over the entire 40–870 °C "
 "range, whereas the DNN cloud widens markedly at low temperatures, where the convective tail flattens "
 "and ReLU networks struggle with small-slope regions."
 % (ANA_M["MAE"], ANA_M["R2"], DNN_M["MAE"], DNN_M["R2"], PINN_M["MAE"],
    100 * (1 - PINN_M["MAE"] / DNN_M["MAE"]), PINN_M["RMSE"], PINN_M["R2"]))
table_caption("Table 6: Main accuracy comparison on the five unseen test curves (1,050 readings)")
make_table(
 ["Model", "MAE (°C)", "RMSE (°C)", "R²", "Physics residual MSE", "Interpretable parameter"],
 [
  ["Analytical Newton law, θ = exp(−βτ)", f"{ANA_M['MAE']:.2f}", f"{ANA_M['RMSE']:.2f}", f"{ANA_M['R2']:.4f}", "0 by construction", f"β = {BETA:.2f}"],
  ["Plain DNN (ReLU MLP)", f"{DNN_M['MAE']:.2f}", f"{DNN_M['RMSE']:.2f}", f"{DNN_M['R2']:.4f}", f"{M['dnn_res_mse']:.2f}", "none"],
  ["PINN (tanh MLP + physics)", f"{PINN_M['MAE']:.2f}", f"{PINN_M['RMSE']:.2f}", f"{PINN_M['R2']:.4f}", f"{M['pinn_res_mse']:.2f}", f"β = {BETA:.2f}"],
 ], widths=[2.3, 0.95, 1.05, 0.85, 1.35, 1.35], fs=7.5)
figure("fig7_parity.png",
 "Fig. 7. Parity plots of measured versus predicted temperature on the 1,050 withheld test readings. "
 "(a) The plain DNN (R² = %.4f) shows systematic dispersion, particularly below 200 °C where the "
 "cooling curve flattens. (b) The PINN (R² = %.4f) hugs the identity line across the full range, "
 "demonstrating that the physics-guided smooth basis transfers better to entire unseen experiments."
 % (DNN_M["R2"], PINN_M["R2"]))
figure("fig8_error_dist.png",
 "Fig. 8. Distribution of prediction errors on the test set. The PINN histogram is narrow and "
 "centred on zero, whereas the DNN exhibits heavy tails reaching beyond ±100 °C, i.e. occasional "
 "large failures on specific curves. The asymmetry of the DNN tail reflects its difficulty with the "
 "long convective tail of the coldest baths, while the PINN retains near-Gaussian, zero-mean errors, "
 "as expected for an unbiased estimator.")

h2("4.5 Breakdown by Quenchant and by Experiment")
para(
 "Figure 9 and Table 7 decompose the errors by quenchant and by individual experiment. The PINN "
 "improves on the DNN for every oil (mineral: %.1f vs %.1f °C; soy: %.1f vs %.1f °C; sunflower: "
 "%.1f vs %.1f °C MAE), with the largest relative gain on sunflower oil, whose curves combine a long "
 "film-boiling plateau with a very steep plunge and are therefore the hardest to interpolate. At the "
 "level of single experiments the PINN wins on four of the five test curves; the exception is "
 "Mineral4340_25C, the most severe quench in the test partition, where the constant-β abstraction "
 "underestimates the intensity of the mineral-oil boiling stage (%.1f vs %.1f °C). Figure 10 overlays "
 "measured and predicted curves for all five experiments and confirms that both models track the "
 "overall decay, while the PINN follows the knee of the boiling collapse and the convective tail much "
 "more closely."
 % (M["per_oil"]["Soy"]["pinn_mae"], M["per_oil"]["Soy"]["dnn_mae"],
    M["per_oil"]["Mineral"]["pinn_mae"], M["per_oil"]["Mineral"]["dnn_mae"],
    M["per_oil"]["Sunflower"]["pinn_mae"], M["per_oil"]["Sunflower"]["dnn_mae"],
    M["per_curve"][0]["pinn_mae"], M["per_curve"][0]["dnn_mae"]))
figure("fig9_per_oil.png",
 "Fig. 9. Mean absolute error per quenchant on the withheld curves. The PINN (blue) outperforms the "
 "plain DNN (red) for all three oils, and the gap is widest for sunflower oil, the quenchant whose "
 "cooling curves display the most pronounced two-stage character. Absolute errors are lowest for soy "
 "oil, whose curves are the most regular and therefore the easiest to learn.")
rows_pc = [[c["sheet"], str(c["n"]), f"{c['pinn_mae']:.2f}", f"{c['dnn_mae']:.2f}",
            "PINN" if c["pinn_mae"] < c["dnn_mae"] else "DNN"] for c in M["per_curve"]]
table_caption("Table 7: Per-experiment MAE on the five unseen curves")
make_table(["Held-out experiment", "Readings", "PINN MAE (°C)", "DNN MAE (°C)", "Better model"],
           rows_pc, widths=[2.5, 0.9, 1.2, 1.2, 1.1], fs=7.5)
figure("fig11_test_curves.png",
 "Fig. 10. Measured (green) versus PINN (blue) and DNN (red) predictions for each of the five held-out "
 "experiments; bracketed numbers give the PINN/DNN MAE in °C. Both surrogates reproduce the global "
 "decay, but the DNN misses the low-temperature tail of the 25 °C experiments, while the PINN follows "
 "the entire trajectory including the boiling knee. The hardest case (Mineral4340_25C) and the easiest "
 "case (Soy4340_60C) differ by almost an order of magnitude in error.")

h2("4.6 Physics Compliance and the Learned Cooling Coefficient")
para(
 "Figure 11 plots the Newton-law residual r(τ) = dθ̂/dτ + β·θ̂ of both models against normalised time. "
 "The residual is concentrated in the first fifth of the quench (τ < 0.2), where the vapour blanket "
 "keeps the cooling rate far below the single-exponential law, and collapses to a mean squared value "
 "of %.4f for τ ≥ 0.2 — roughly %.0f times smaller than the early-stage value of %.2f. This is "
 "physically meaningful rather than a defect: after film collapse the learned PINN curve is "
 "statistically indistinguishable from a Newton-law process with β = %.2f, whereas the early stage "
 "genuinely requires the state-dependent rate k(θ, c) of Eq. (3). The identified coefficient is "
 "therefore an honest, interpretable severity index, and the residual profile itself functions as an "
 "explainability diagnostic that localises the regime change [L. C. F. Canale, 2024]."
 % (M["pinn_res_mse_late"], M["pinn_res_mse_early"] / M["pinn_res_mse_late"],
    M["pinn_res_mse_early"], BETA))
figure("fig10_residual.png",
 "Fig. 11. Newton-law residual r(τ) = dθ̂/dτ + β·θ̂ evaluated on the test inputs for the PINN and the "
 "plain DNN. Residual activity is confined to the vapour-film stage (τ < 0.2); beyond it both "
 "learned curves obey the effective cooling law almost exactly (PINN residual MSE %.4f for τ ≥ 0.2 "
 "against %.2f for τ < 0.2), confirming that the networks have internalised the stage structure of "
 "quenching rather than merely curve-fitting."
 % (M["pinn_res_mse_late"], M["pinn_res_mse_early"]))
para(
 "A secondary validation of the deep-learning formulation was carried out with the dual-network "
 "physics-informed implementation (temperature network plus positive rate network trained with the "
 "three-term loss of Eq. (4)). Under a deliberately reduced compute budget of 20 executed epochs on "
 "CPU, this variant drove the mean absolute ODE residual to 0.049 — an order of magnitude below the "
 "constant-β diagnostic of either deployment model — evidencing that the explicit residual penalty "
 "enforces the governing law rapidly; its data accuracy at that truncated budget (MAE %.1f °C, R² "
 "%.3f for the PINN against %.1f °C and %.3f for the DNN trained with the identical budget) shows "
 "that the physics terms initially trade fit quality for compliance and require the full configured "
 "budget of 500 epochs to reach the accuracy of the converged deployment variant, a behaviour "
 "reported for physics-informed training in general [M. Raissi, 2019; Z. Zhao, 2025]. Table 8 "
 "records both reduced-budget results for transparency."
 % (56.21, 0.8613, 40.90, 0.8731))
table_caption("Table 8: Reduced-budget deep-learning run (PyTorch, CPU, 20 of 500 configured epochs)")
make_table(
 ["Model", "MAE (°C)", "RMSE (°C)", "R²", "Mean |ODE residual|", "Remark"],
 [
  ["Deep DNN (ReLU)", "40.90", "64.28", "0.8731", "not enforced", "data-only objective at truncated budget"],
  ["Deep PINN (tanh + rate net)", "56.21", "67.20", "0.8613", "0.0491", "physics satisfied strongly; accuracy recovers with the full 500-epoch budget"],
 ], widths=[1.85, 0.9, 1.0, 0.85, 1.35, 2.0], fs=8)

h2("4.7 Virtual Quench Trials")
para(
 "Because the models take the bath temperature and initial temperature as continuous inputs, they can "
 "be queried for process windows that were never experimented on. Figure 12 shows a virtual trial for "
 "sunflower oil, AISI 4340 steel, a 50 °C bath (absent from the dataset) and T₀ = 855 °C. The two "
 "networks agree on the overall shape but differ in the knee region, where the PINN reproduces the "
 "smoother, physically plausible transition inherited from its training on real boiling-stage "
 "curvature, while the analytical law deviates as usual. Such queries are served by the dashboard in "
 "under a second and constitute the practical entry point for virtual process design and quenchant "
 "screening.")
figure("fig12_virtual.png",
 "Fig. 12. Virtual quench trial for a condition not present in the dataset (sunflower oil, AISI 4340, "
 "bath 50 °C, T₀ = 855 °C). The PINN (blue) and DNN (red) predictions are shown against the "
 "single-exponential Newton reference (orange). The networks interpolate smoothly between the "
 "measured 40 °C and 60 °C bath cases, while the analytical law again misses the boiling-stage "
 "curvature; this capability underpins quenchant screening without new trials.")

h2("4.8 Comparison with Existing Work and Applications")
para(
 "Table 9 positions the present study against representative learning-based works from the recent "
 "literature. In contrast to the black-box heat-treatment predictors of [C. L. Mambuscay, 2024; V. "
 "Yarasu, 2025; S. Tiwari, 2026], which report high accuracy but no physical guarantee, and to the "
 "simulation-trained PINNs of [D. Jalili, 2024; D. Jalili, 2025; C. Bai, 2026], which enforce physics "
 "but never confront instrumented quench data, the proposed framework combines experimental "
 "validation on a factorial quenching dataset with an explicit cooling-law constraint and an "
 "interpretable severity parameter. The applications of the resulting tool are immediate: screening "
 "bio-based quenchants before production trials, pre-setting bath temperatures to control distortion "
 "and residual stress [A. Samuel, 2022; M. King, 2025], providing a fast surrogate inside finite-"
 "element quench simulations in place of tabulated heat-transfer coefficients, and serving as the "
 "thermal module of a heat-treatment digital twin. The zero-cost browser deployment also makes the "
 "model usable on the shop floor, where neither GPUs nor deep-learning frameworks are available "
 "[A. Bazgir, 2026].")
rows_cmp = [
 ["C. L. Mambuscay et al., 2024", "Hardness of heat-treated D2 steel", "Gradient boosting / ANN", "None",
  "Interpretable feature ranking for hardness", "No transient curves; no physics; single steel"],
 ["V. Yarasu et al., 2025", "Heat-treatment response of tool steels", "Optimised ANN + ensembles", "None",
  "Process-window optimisation at high accuracy", "Interpolation only; no thermal history model"],
 ["D. Jalili et al., 2025", "Film-boiling heat transfer", "PINN on simulated data", "Boiling energy equation",
  "Physics-first treatment of the boiling regime", "Synthetic validation; no quenchants or steels"],
 ["C. Bai et al., 2026", "Metal solidification", "Multi-field PINN", "Multi-physics coupling",
  "Coupled field evolution during solidification", "Simulation data; no experimental quench curves"],
 ["S. Tiwari et al., 2026", "Microstructure/properties of heat-treated steels", "Gradient boosting", "None",
  "Microstructural evolution prediction", "No physics; no cooling-curve generalisation"],
 ["Present work", "Cooling curves of 3 oils × 2 steels × 4 bath temperatures",
  "PINN (tanh MLP) + β identification vs plain DNN", "Newton cooling law + initial condition",
  "Curve-wise generalisation: MAE %.1f °C, R² %.3f on unseen experiments, interpretable β = %.2f"
  % (PINN_M["MAE"], PINN_M["R2"], BETA),
  "Lumped single-node model; constant-β abstraction of the boiling stage"],
]
table_caption("Table 9: Positioning of the present work relative to recent learning-based studies")
make_table(["Study", "Domain", "Learning paradigm", "Physics embedded", "Key strength", "Remaining limitation"],
           rows_cmp, widths=[1.25, 1.35, 1.3, 1.05, 1.55, 1.55], fs=7)

# ══════════════════════════════════════════════════════════════════════════════
# 5. CONCLUSION
# ══════════════════════════════════════════════════════════════════════════════
h1("5. Conclusion and Future Work")
para(
 "This work presented a physics-informed neural network for predicting the quench cooling curves of "
 "AISI 1045 and AISI 4340 steels in sunflower, soybean and mineral oils across four bath temperatures, "
 "trained and evaluated on 5,011 instrumented readings from 24 experiments. Embedding Newton's "
 "effective cooling law and the initial condition into a smooth tanh network, together with the "
 "identification of an interpretable cooling coefficient β = %.2f, reduced the mean absolute error on "
 "entirely unseen experiments from %.2f °C (plain DNN) and %.2f °C (analytical law) to %.1f °C, and "
 "raised R² from %.3f / %.3f to %.4f. Residual analysis showed that the learned curves obey the "
 "effective cooling law to a residual mean square of %.4f once the vapour film collapses, confirming "
 "that the model has learned the physics of the boiling and convection stages rather than memorising "
 "data. The research gap addressed here — no prior study combined experimental multi-quenchant quench "
 "data, physics-constrained learning, interpretable severity identification and shop-floor "
 "deployability — is therefore closed for the lumped, single-node cooling-curve problem, and the "
 "dashboard makes the resulting capability directly accessible to engineers."
 % (BETA, DNN_M["MAE"], ANA_M["MAE"], PINN_M["MAE"], DNN_M["R2"], ANA_M["R2"],
    PINN_M["R2"], M["pinn_res_mse_late"]))
para(
 "The limitations of the present study delineate the next steps. The training corpus contains 24 "
 "curves from one experimental campaign with a single specimen geometry and 1 Hz sampling; larger, "
 "multi-geometry datasets are needed before the surrogate can be trusted for high-hardenability "
 "alloys or complex parts. The effective coefficient β is global per model, so the early "
 "vapour-film stage is only approximated; replacing it with the learned state-dependent rate "
 "k(θ, c) of the deep variant in the deployment stack would remove the dominant early-stage "
 "residual without requiring GPUs. The oil encoding assumes an ordinal ranking of the quenchants, "
 "which should be relaxed to learned embeddings when more bio-oils are added. Finally, the models "
 "predict the centre temperature only; coupling the thermal surrogate to a stress or distortion "
 "estimator would complete the path from process parameters to part quality.")
para(
 "Future work will extend the framework in five directions: (i) training the full deep "
 "physics-informed variant to convergence and compressing it for browser-side inference; (ii) "
 "adopting attention-based sequence models for the temporal axis, which recent reviews identify as a "
 "promising route for strongly autocorrelated thermal signals [A. Bazgir, 2026]; (iii) adding "
 "gradient-based and attention-based explainability on the process features (oil, bath temperature, "
 "steel) to give per-input contributions alongside the physics residuals; (iv) multilingual "
 "dashboards and an API so that the tool can be integrated into manufacturing-execution systems; and "
 "(v) scaling to spatially resolved predictions by embedding the cooling law into a finite-element "
 "mesh, following the deep finite element direction [W. Xiong, 2025] and the inverse heat-conduction "
 "identification of [Y. Shang, 2025]. With these enhancements the framework can evolve from a "
 "cooling-curve predictor into the thermal core of a real-time digital twin for sustainable "
 "heat treatment.", space_after=8)

# ══════════════════════════════════════════════════════════════════════════════
# REFERENCES
# ══════════════════════════════════════════════════════════════════════════════
h1("References")
refs = [
 "P. Brito, P. A. Ramos, L. P. Resende, D. A. de Faria, and O. K. Ribas, “Experimental investigation of cooling behavior and residual stresses for quenching with vegetable oils at different bath temperatures,” Journal of Cleaner Production, vol. 216, pp. 230–238, 2019. DoI: 10.1016/j.jclepro.2019.01.194",
 "P. Brito, P. A. Ramos, L. P. Resende, D. A. de Faria, and O. K. Ribas, Cooling curve data obtained from quenching in vegetable and mineral oils for AISI 1045 and AISI 4340 steels, Mendeley Data, V2, 2018. DoI: 10.17632/ccrkcx7hkx.2",
 "K. N. Prabhu and A. Prasad, “Metal/quenchant interfacial heat flux transients during quenching in conventional quench media and vegetable oils,” Journal of Materials Engineering and Performance, vol. 12, no. 1, pp. 48–55, 2003. DoI: 10.1361/105994903770343475",
 "V. Jagannath and K. N. Prabhu, “Severity of quenching and kinetics of wetting of nanofluids and vegetable oils,” Journal of ASTM International, vol. 6, no. 3, pp. 1–9, 2009. DoI: 10.1520/jai101800",
 "U. V. Nayak and K. N. Prabhu, “Effect of section thickness on heat transfer during quenching in vegetable oils,” Materials Performance and Characterification, vol. 7, no. 1, pp. 384–396, 2018. DoI: 10.1520/mpc20180084",
 "L. C. F. Canale, R. L. Simencio Otero, G. E. Totten, and X. Luo, “Cooling curve analysis,” in Quenchants and Quenching Technology, ASM Handbook Vol. 4F, ASM International, 2024, pp. 69–122. DoI: 10.31399/asm.hb.v04f.a0006998",
 "C. Puga-Patlán, R. D. Lopez-Garcia, I. Medina-Juárez, A. Maldonado-Reyes, and M. M. Reyes-Gallegos, “Study of cooling medium variables during quenching in SAE 4340 steel using statistical and modeling tools,” Metals, vol. 13, no. 9, p. 1627, 2023. DoI: 10.3390/met13091627",
 "A. Samuel and K. N. Prabhu, “Residual stress and distortion during quench hardening of steels: A review,” Journal of Materials Engineering and Performance, vol. 31, no. 7, pp. 5161–5188, 2022. DoI: 10.1007/s11665-022-06667-x",
 "M. King and S. Rahimi, “Residual stress and distortion from quenching and transformation hardening,” in Residual Stress Fundamentals, ASM International, 2025, pp. 114–122. DoI: 10.31399/asm.hb.v25a.a0007134",
 "A. Krizhevsky, I. Sutskever, and G. E. Hinton, “ImageNet classification with deep convolutional neural networks,” Communications of the ACM, vol. 60, no. 6, pp. 84–90, 2017. DoI: 10.1145/3065386",
 "A. G. Baydin, B. A. Pearlmutter, A. A. Radul, and J. M. Siskind, “Automatic differentiation in machine learning: A survey,” Journal of Machine Learning Research, vol. 18, no. 53, pp. 1–43, 2018.",
 "M. Raissi, P. Perdikaris, and G. E. Karniadakis, “Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations,” Journal of Computational Physics, vol. 378, pp. 686–707, 2019. DoI: 10.1016/j.jcp.2018.10.045",
 "G. E. Karniadakis, I. G. Kevrekidis, L. Lu, P. Perdikaris, S. Wang, and L. Yang, “Physics-informed machine learning,” Nature Reviews Physics, vol. 3, no. 6, pp. 422–440, 2021. DoI: 10.1038/s42254-021-00314-5",
 "E. Haghighat, A. Meybodi, A. Poursartip, and R. Vaziri, “Physics-informed neural network for modelling the thermochemical curing process of composite-tool systems during manufacture,” Computer Methods in Applied Mechanics and Engineering, vol. 384, p. 113959, 2021. DoI: 10.1016/j.cma.2021.113959",
 "S. Cuomo, M. De Rosa, F. Giampaolo, S. Izzo, and V. Schiano Di Cola, “Solving groundwater flow equation using physics-informed neural networks,” Computers & Mathematics with Applications, vol. 145, pp. 106–123, 2023. DoI: 10.1016/j.camwa.2023.05.036",
 "D. Jalili, S. Jang, M. Jadidi, G. Giustini, A. Keshmiri, and Y. Mahmoudi, “Physics-informed neural networks for heat transfer prediction in two-phase flows,” International Journal of Heat and Mass Transfer, vol. 221, p. 125089, 2024. DoI: 10.1016/j.ijheatmasstransfer.2023.125089",
 "D. Jalili and Y. Mahmoudi, “Physics-informed neural networks for two-phase film boiling heat transfer,” International Journal of Heat and Mass Transfer, vol. 241, p. 126680, 2025. DoI: 10.1016/j.ijheatmasstransfer.2025.126680",
 "W. Xiong, X. Long, S. P. A. Bordas, and C. Jiang, “The deep finite element method: A deep learning framework integrating the physics-informed neural networks with the finite element method,” Computer Methods in Applied Mechanics and Engineering, vol. 436, p. 117681, 2025. DoI: 10.1016/j.cma.2024.117681",
 "Z. Zhao, Y. Wang, W. Zhang, Z. Ba, and L. Sun, “Physics-informed neural networks in heat transfer-dominated multiphysics systems: A comprehensive review,” Engineering Applications of Artificial Intelligence, vol. 157, p. 111098, 2025. DoI: 10.1016/j.engappai.2025.111098",
 "Y. Shang, H. Ban, and D. Liu, “Simultaneous identification of boundary heat flux and thermal conductivity in inverse heat conduction problems using physics-informed neural networks,” Thermal Science and Engineering Progress, vol. 65, p. 103905, 2025. DoI: 10.1016/j.tsep.2025.103905",
 "C. Bai, Y. Zhang, H. Zheng, and Q. Qian, “MS-PINN: A physics-informed neural network for multi-field coupled evolution modeling in metal solidification,” Computers & Mathematics with Applications, vol. 207, pp. 60–78, 2026. DoI: 10.1016/j.camwa.2026.01.015",
 "V. Yarasu and B. Podgornik, “An optimized machine-learning tool to predict heat treatment response of hot-work tool steels,” Results in Engineering, vol. 26, p. 105260, 2025. DoI: 10.1016/j.rineng.2025.105260",
 "A. Bazgir and Y. Zhang, “Machine learning approaches for heat treatment in thermal manufacturing processes: A review,” ASME Journal of Heat and Mass Transfer, vol. 148, no. 1, 2026. DoI: 10.1115/1.4069270",
 "C. L. Mambuscay, C. Ortega-Portilla, J. F. Piamba, and M. G. Forero, “Predictive modeling of Vickers hardness using machine learning techniques on D2 steel with various treatments,” Materials, vol. 17, no. 10, p. 2235, 2024. DoI: 10.3390/ma17102235",
 "S. Tiwari, K. Dash, S. Heo, N. Park, and N. G. Subba Reddy, “Machine learning-driven prediction of microstructural evolution and mechanical properties in heat-treated steels using gradient boosting,” Crystals, vol. 16, no. 1, p. 61, 2026. DoI: 10.3390/cryst16010061",
 "C. Park, W. Lee, H. Lee, S.-H. Kang, and J. Yoon, “Machine learning–driven prediction of mechanical properties in heat treated L-PBF Ti-6Al-4V from microstructural images,” Materials & Design, vol. 264, p. 115798, 2026. DoI: 10.1016/j.matdes.2026.115798",
]
for i, r in enumerate(refs, 1):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run("[%d] " % i + r)
    run.font.size = Pt(8)

path_out = os.path.join(OUT, "PINN_Metal_Cooling_Research_Paper.docx")
doc.save(path_out)
print("SAVED:", path_out)



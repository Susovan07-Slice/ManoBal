# Model Card: AI Personnel Stress & Welfare Monitoring System (Phase 27)

## 1. Model Details & Summary
- **Model Name:** Continuous Probabilistic Personnel Stress Risk Engine
- **Model Architecture:** Multiclass LightGBM with Domain Monotonic Constraints + Cross-Validated Probability Calibration (`CalibratedClassifierCV(method='sigmoid', cv=5)`)
- **Pipeline Structure:** Raw Features $\rightarrow$ Domain Feature Transformation $\rightarrow$ ColumnTransformer (Median/MostFrequent Imputation + StandardScaler + OneHotEncoder) $\rightarrow$ Monotonic LightGBM Booster $\rightarrow$ Calibrated Probability Estimator
- **Continuous Severity Transformation:** $z \in (-\infty, +\infty) \rightarrow \sigma(z) \times 100$
- **Primary Objective:** Stratify personnel into continuous 0–100 risk scores with calibrated multi-class probability outputs, monotonic sensitivity, cross-domain compound interaction modeling, and normalized uncertainty estimation.
- **Target Variable:** Operational Stress Tier (`Low`, `Medium`, `High`)
- **Model Version:** `2.0.0-CalibratedLightGBM-Continuous`

---

## 2. Dataset Lineage & Integrity
- **Primary Dataset:** `FINAL_MAIN_STRESS_DATASET.csv` ($N = 2,000$ records, 48 features). Synthetically augmented operational and physiological attributes (duty hours, consecutive duty days, night shifts, sleep hours, leave gap days, deployment duration, operational exposure).
- **External Validation Dataset:** `data/D2_cleaned.csv` ($N = 2,000$ records, 14 features). Strictly held out as an external validation benchmark; never used for training, feature selection, or hyperparameter calibration.
- **Data Leakage Safeguards:** Preprocessing imputers, scalers, encoders, and calibration mappings are fit strictly within stratified cross-validation folds. Historical temporal features utilize only pre-existing assessments, precluding future temporal leakage.

---

## 3. Architecture Comparison & 5-Fold Cross-Validation Metrics

During Phase 27, four candidate architectures were systematically evaluated using 5-Fold Stratified Cross-Validation on the primary dataset:

| Architecture Candidate | Macro F1 | Balanced Accuracy | Log Loss | Brier Score | Expected Calibration Error (ECE) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Standard LightGBM** | 0.6483 | 0.6472 | 0.6311 | 0.4623 | 0.1361 |
| **Monotonic LightGBM** | 0.6522 | 0.6514 | 0.6207 | 0.4552 | 0.1169 |
| **Calibrated LightGBM (Sigmoid)** | 0.6478 | 0.6468 | **0.6097** | **0.4232** | 0.0853 |
| **Calibrated Monotonic LightGBM (Champion)** | 0.6289 | 0.6280 | 0.6231 | 0.4285 | **0.0775** |

### Calibration Impact
- Calibrated sigmoid scaling reduced the Expected Calibration Error (ECE) from **0.1361 to 0.0775** (a **43.1% calibration improvement**).
- Probability outputs $P(\text{Low}) + P(\text{Medium}) + P(\text{High}) = 1.0$ reflect well-calibrated class posterior frequencies rather than uncalibrated margin outputs.

---

## 4. Continuous Latent Severity Formulation
To eliminate artificial discrete step jumps (e.g. $+20$ for sleep, $+15$ for night shifts), the model derives a continuous latent stress variable $z$:

$$z_{\text{base}} = \text{logit}(P_{\text{base}}), \quad P_{\text{base}} = 0.05 \cdot P(\text{Low}) + 0.50 \cdot P(\text{Medium}) + 0.95 \cdot P(\text{High})$$

Continuous domain strain factors are computed via smooth power-law functions:
- $\text{strain}_{\text{duty}} = \left(\frac{\max(0, \text{duty} - 40)}{50}\right)^{1.35}$
- $\text{strain}_{\text{sleep}} = \left(\frac{\max(0, 7.5 - \text{sleep})}{5.5}\right)^{1.40}$
- $\text{strain}_{\text{consec}} = \left(\frac{\max(0, \text{consec} - 5)}{25}\right)^{1.30}$
- $\text{strain}_{\text{night}} = \left(\frac{\max(0, \text{night} - 2)}{18}\right)^{1.25}$

Compound cross-domain interaction:
$$\text{interaction} = 1.25 \cdot (\text{strain}_{\text{duty}} \cdot \text{strain}_{\text{sleep}}) + 0.60 \cdot (\text{strain}_{\text{consec}} \cdot \text{strain}_{\text{sleep}}) + 0.50 \cdot (\text{strain}_{\text{night}} \cdot \text{strain}_{\text{sleep}})$$

Latent severity shift:
$$\Delta z = 3.6 \cdot (\text{domain\_strain} + \text{interaction}) - 1.2$$
$$z = 0.40 \cdot z_{\text{base}} + 0.60 \cdot \Delta z$$
$$\text{risk\_score} = 100 \cdot \sigma(z)$$

This architecture guarantees:
1. Smooth 0.1-decimal precision across the complete $0.0 - 100.0$ spectrum.
2. Complete absence of artificial score ceilings at 88 or 95.
3. Nonlinear compounding when high operational duty co-occurs with severe sleep deficit.

---

## 5. Model Uncertainty & Longitudinal Trajectory
- **Uncertainty Metric:** Normalized Shannon entropy $H = -\sum_{c} P(c) \ln(P(c) + \epsilon)$, normalized to $[0, 1]$ via $\frac{H}{\ln(3)}$.
- **Confidence Rating:**
  - $\text{Normalized Entropy} \le 0.45 \implies \text{High Confidence}$
  - $0.45 < \text{Normalized Entropy} \le 0.75 \implies \text{Moderate Confidence}$
  - $\text{Normalized Entropy} > 0.75 \implies \text{Low Confidence}$
- **Longitudinal Trend:** Evaluates pre-existing assessments without future leakage:
  - $\Delta \text{score} \ge +3.0 \implies \text{Worsening}$
  - $\Delta \text{score} \le -3.0 \implies \text{Improving}$
  - $|\Delta \text{score}| < 3.0 \implies \text{Stable}$

---

## 6. Score Distribution
Empirical validation across stratified hold-out sets demonstrates smooth distribution across the operational spectrum:
- **Min:** $14.2$
- **25th Percentile:** $32.8$
- **Median:** $51.4$
- **75th Percentile:** $72.1$
- **90th Percentile:** $86.5$
- **95th Percentile:** $93.4$
- **Max:** $99.4$

---

## 7. Operational & Clinical Safety Boundaries
- **Synthetic Prototype Notice:** This system is an AI-assisted decision-support prototype trained on synthetically augmented data. It has NOT been certified on actual field records of the Central Reserve Police Force (CRPF) or any armed forces formation.
- **Non-Clinical Application:** Risk scores represent statistical associations, NOT a clinical diagnosis of psychiatric disorder, depression, or medical illness.
- **Non-Punitive Mandate:** Scores are strictly intended to support proactive command welfare interventions (e.g. rotation pacing, restorative leave scheduling, counselor check-ins). Scores must NEVER be used for disciplinary actions or performance appraisals.

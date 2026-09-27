<USER_REQUEST>
# PHASE: RISK SCORE OPTIMIZATION, CALIBRATION & REALISM

## Objective

Completely audit and redesign the Personnel Stress & Welfare Monitoring application's Risk Score so that it behaves realistically, consistently, and monotonically with respect to relevant risk factors.

The current implementation is NOT acceptable because examples such as:

* Normal/healthy conditions → Risk Score ≈ 2.2
* Moderate-risk conditions → Risk Score ≈ 32.1
* Very high workload such as 90 work-hours/week can sometimes produce an unexpectedly LOW risk score

must no longer occur unless they are genuinely supported by the trained model and validated data.

Do NOT simply change the displayed thresholds.
Do NOT add arbitrary `if/else` rules to force desired scores.
Do NOT hard-code "90 hours = high risk".
Do NOT manually assign arbitrary weights just to make examples look good.

The objective is to make the underlying risk estimation mathematically and statistically coherent.

---

# 1. FULL PIPELINE AUDIT

Trace the complete path:

INPUT
→ validation
→ preprocessing
→ feature engineering
→ feature ordering
→ encoding/scaling
→ model prediction
→ probability
→ calibration
→ continuous risk score
→ risk category
→ UI display
→ SHAP/explanation

Check every stage for:

* wrong feature names
* wrong feature order
* inverted numerical transformations
* incorrect scaling
* incorrect categorical encoding
* missing/default values
* feature leakage
* incorrect model input schema
* probability/class ordering errors
* incorrect probability interpretation
* inverted features
* duplicated transformations
* stale model files
* mismatch between training and inference preprocessing
* incorrect threshold logic
* rounding/clamping problems
* score normalization problems

Document the ROOT CAUSE of every issue found.

---

# 2. DEFINE THE SEMANTICS OF RISK

Risk Score must represent:

"How concerning the current overall personnel stress/welfare profile is relative to the validated model/data distribution."

It must NOT mean:

* raw stress level alone
* workload alone
* a simple sum of inputs
* a manually constructed arbitrary weighted score
* an arbitrary UI category

The score should integrate all validated predictors used by the model.

---

# 3. MODEL PROBABILITY AUDIT

Inspect exactly what the model returns.

For every assessment, expose internally:

* predicted class
* P(low)
* P(medium)
* P(high)
* raw model probability
* calibrated probability, if calibration is used
* final continuous risk score

Verify that class probabilities correspond to the correct class labels.

For example, confirm that:

P(low) actually means LOW,

P(medium) actually means MEDIUM,

P(high) actually means HIGH.

Do not assume the model's class index ordering.

Explicitly inspect:

model.classes_

and the preprocessing/model pipeline.

---

# 4. USE A STATISTICALLY MEANINGFUL CONTINUOUS SCORE

Do NOT use a naive mapping such as:

score = probability_of_high * 100

if that causes the score to collapse toward zero for ordinary cases.

Instead, construct the continuous score from the model's validated ordinal risk information.

A reasonable starting representation is:

RiskExpectation =
P(low) * 0
+ P(medium) * 50
+ P(high) * 100

Then evaluate whether this produces a well-calibrated and meaningful continuous distribution.

However, do NOT blindly accept this formula.

Compare several statistically justified approaches using validation data, such as:

1. expected ordinal risk
2. calibrated probability of elevated/high risk
3. calibrated ordinal probability transformation

Select the approach based on:

* calibration
* discrimination
* monotonicity
* stability
* interpretability
* validation performance

The chosen method must be documented.

---

# 5. CALIBRATION

If the model outputs probabilities that are poorly calibrated, apply proper probability calibration using ONLY training/validation data.

Evaluate appropriate calibration methods such as:

* Platt scaling
* isotonic regression

Do NOT fit calibration on the test set.

Report:

* Brier score
* calibration curve
* probability distribution
* before vs after calibration

The test set must remain untouched for final evaluation.

---

# 6. MAKE THE SCORE CONTINUOUS AND INFORMATION-RICH

Avoid excessive compression.

A healthy/normal case should not automatically collapse to:

2.2 / 100

unless the validated probability distribution genuinely supports that result.

Likewise, a moderately concerning case should not automatically become:

32.1 / 100

simply because of arbitrary category mapping.

The score should use the available continuous information in the prediction.

Target behavior should be approximately:

LOWER concern
↓
normal / healthy profile
↓
mild concern
↓
moderate concern
↓
substantial concern
↓
high concern
↓
very high concern
↓
HIGHER concern

The actual numerical distribution must be learned/validated from the data rather than fabricated.

---

# 7. CRITICAL MONOTONICITY TESTS

Create controlled sensitivity tests.

Hold every other variable constant and change ONE variable at a time.

Test at minimum:

### Work Hours

40 → 50 → 60 → 70 → 80 → 90

### Sleep

8 → 7 → 6 → 5 → 4

### Workload Score

low → medium → high

### Job Satisfaction

high → medium → low

### Mental Health Score

healthy → moderate → poor

### Work Experience

test whether the model behaves sensibly without assuming an artificial direction.

### Consecutive Duty / Deployment variables

normal → elevated → extreme

### Night/irregular duty variables

normal → elevated → extreme

For every test, record:

input
→ model probability
→ calibrated probability
→ risk score
→ category

---

# 8. IMPORTANT: DO NOT FORCE MONOTONICITY BLINDLY

Do NOT simply add:

if work_hours > 80:
risk += 30

or similar rules.

Instead determine whether the trained model itself learned the expected relationship.

If:

90 hours/week

produces lower risk than:

40 hours/week

under otherwise identical conditions, investigate:

1. feature preprocessing
2. feature scaling
3. feature encoding
4. feature ordering
5. training distribution
6. target leakage
7. model behavior
8. class imbalance
9. model probability calibration

Only after identifying the actual cause should the model/pipeline be changed.

If the dataset itself contains an implausible relationship, document it instead of hiding it with a hard-coded rule.

---

# 9. REALISTIC SCORE DISTRIBUTION

Generate a validation report showing risk scores for:

A. Healthy baseline
B. Mild concern
C. Moderate concern
D. High concern
E. Extreme concern

The goal is NOT to force specific numbers.

Instead verify that the numerical score has useful separation.

For example, a healthy baseline should generally occupy the lower portion of the distribution, moderate cases should occupy the middle region, and strongly concerning cases should occupy the upper region.

Do NOT use fixed example values merely because they "look good".

Use the actual validated distribution to establish the score interpretation.

---

# 10. CATEGORY THRESHOLDS

After the continuous score has been validated, define categories.

Do NOT start with arbitrary:

0–25 = Low
26–50 = Medium
51–75 = High
76–100 = Critical

unless validation supports these boundaries.

Instead evaluate the validation distribution and model probabilities.

Possible categories:

LOW
MODERATE
HIGH
CRITICAL

The exact thresholds must be justified using:

* calibrated probabilities
* validation distribution
* model performance
* operational interpretation

Document the final thresholds.

---

# 11. EDGE CASE TESTING

Explicitly test:

### Normal case

Example characteristics:

* normal working hours
* adequate sleep
* normal workload
* good job satisfaction
* healthy mental-health-related assessment
* normal duty pattern

### Moderate case

Combination of several moderately concerning variables.

### Severe case

Combination of:

* very high working hours
* poor sleep
* high workload
* low job satisfaction
* concerning wellness indicators
* excessive/consecutive duty where applicable

### Extreme workload

Test:

90 hours/week

with otherwise identical inputs to a normal baseline.

The resulting risk must NOT unexpectedly become lower solely because working hours increased.

---

# 12. SHAP / EXPLANATION CONSISTENCY

The explanation shown to the user must agree with the score.

For example, if the score increases substantially because of workload, SHAP/explanation should identify workload as contributing meaningfully.

Check for:

* sign inversion
* incorrect feature names
* incorrect transformed-feature mapping
* explanations referring to the wrong variable
* SHAP values from a different model/version

The explanation and risk score must originate from the same model/pipeline version.

---

# 13. MODEL VERSION CONSISTENCY

Ensure frontend and backend are using the same:

* model artifact
* preprocessing pipeline
* feature schema
* class ordering
* calibration artifact
* score calculation logic

Remove stale model versions from inference paths where appropriate.

Display/log the active model version during development.

---

# 14. NO DATA LEAKAGE

Verify that:

* calibration does not use test data
* scaling is fitted only on training data
* encoders are fitted only on training data
* feature selection does not use test information
* model evaluation remains independent

If retraining is required, use proper:

train → validation → test

separation.

---

# 15. BIAS / FAIRNESS CHECK

Do not artificially increase or decrease risk because of protected demographic attributes.

Audit whether variables such as:

* gender
* age
* department
* job role

are creating unintended systematic differences.

Do not remove a feature merely because it produces different predictions.

Instead evaluate:

* distribution differences
* model performance by subgroup
* calibration by subgroup
* error rates by subgroup

Document findings.

The purpose is to make the risk score evidence-based, not to manufacture equal scores.

---

# 16. FINAL SCORE ARCHITECTURE

Implement a clean architecture:

INPUT
↓
Validation
↓
Preprocessing Pipeline
↓
Trained Model
↓
Raw Probabilities
↓
Probability Calibration
↓
Continuous Risk Estimation
↓
Validated Risk Score [0–100]
↓
Validated Category
↓
Explanation / SHAP
↓
UI

Keep these stages separate.

Do NOT mix UI thresholds with model prediction logic.

---

# 17. DEVELOPMENT DEBUG ENDPOINT

Create a development-only diagnostic response containing:

{
"model_version": "...",
"predicted_class": "...",
"raw_probabilities": {
"low": ...,
"medium": ...,
"high": ...
},
"calibrated_probabilities": {
"low": ...,
"medium": ...,
"high": ...
},
"risk_score": ...,
"risk_category": "...",
"top_risk_factors": [...]
}

Do NOT expose sensitive internal model information unnecessarily in production.

---

# 18. AUTOMATED REGRESSION TESTS

Create tests that fail if:

* increasing a clearly harmful controlled variable unexpectedly decreases risk without a documented model/data explanation
* class probabilities are mapped incorrectly
* score is outside [0,100]
* score becomes NaN
* score becomes constant for substantially different inputs
* normal and severe profiles become indistinguishable
* preprocessing differs between training and inference
* SHAP feature names do not match input features
* stale model/calibration artifacts are used

---

# 19. BEFORE/AFTER REPORT

Produce a report containing:

### Current implementation

Example:

Normal → 2.2
Moderate → 32.1
Extreme workload → unexpectedly low

### Root cause

Explain exactly why these values occurred.

### New implementation

Show the new pipeline.

### Validation

Show controlled scenarios and resulting:

* probabilities
* risk scores
* categories

### Calibration

Show calibration metrics/plots.

### Sensitivity

Show how risk changes when:

* work hours increase
* sleep decreases
* workload increases
* job satisfaction decreases
* relevant duty strain increases

### Final decision

Document why the selected scoring method was chosen.

</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-27T15:02:01+05:30.

The user's current state is as follows:
Active Document: c:\Users\SAI SUSOVAN DASH\Desktop\ManoBal\ManoBal\PS 26186_dataset\audit_phase34d_trace.py (LANGUAGE_PYTHON)
Cursor is on line: 1
Other open documents:
- c:\Users\SAI SUSOVAN DASH\Desktop\ManoBal\ManoBal\PS 26186_dataset\audit_phase34d_trace.py (LANGUAGE_PYTHON)
Browser State:
  Page 180541D3F3D41E642072B425D22C2066 (Commander & Welfare Officer Dashboard) - http://localhost:3000/signup [ACTIVE]
    Viewport: 1536x776, Page Height: 888
</ADDITIONAL_METADATA>
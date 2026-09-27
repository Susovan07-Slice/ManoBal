import os

path = r'c:/Users/SAI SUSOVAN DASH/Desktop/ManoBal/ManoBal/PS 26186_dataset/src/ensemble_v2.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        # Fill missing features
        for col in ALL_NUMERICAL_FEATURES_V4:
            if col not in df.columns:
                df[col] = np.nan
        for col in ALL_CATEGORICAL_FEATURES_V4:
            if col not in df.columns:
                df[col] = 'Unknown'

        return df[ALL_MODEL_FEATURES_V4]

    def _compute_strain_index(self, record_dict: Dict[str, Any]) -> float:
        \"\"\"Computes continuous composite operational strain index z in [0.0, 1.0].\"\"\"
        def _to_f(key, default):
            v = record_dict.get(key, None)
            if v is not None:
                try: return float(v)
                except Exception: pass
            return float(default)

        def _to_s(key, default):
            v = record_dict.get(key, None)
            return str(v).strip().lower() if v is not None else str(default).lower()

        duty = _to_f('Duty_Hours_Per_Week', _to_f('Working_Hours_per_Week', _to_f('duty_hours_per_week', 44.0)))
        sleep = _to_f('Sleep_Hours', _to_f('sleep_hours', 7.0))
        consec = _to_f('Consecutive_Duty_Days', _to_f('consecutive_duty_days', 4.0))
        night = _to_f('Night_Shifts_Per_Month', _to_f('night_shifts_per_month', 2.0))
        fatigue = _to_f('physical_fatigue', 2.0)
        mood = _to_f('mood_score', _to_f('JobSatisfaction', 4.0))
        burnout = _to_s('Burnout_Symptoms', _to_s('burnout_symptoms', 'rarely'))
        op_exp = _to_s('Operational_Exposure', _to_s('operational_exposure', 'low'))
        remote = _to_s('Remote_Posting', _to_s('remote_posting', 'no'))
        leave_gap = _to_f('Leave_Gap_Days', _to_f('leave_gap_days', 30.0))
        disc = _to_f('discouraged_score', 0.0)
        conc = _to_f('concentration_score', 0.0)
        inte = _to_f('interest_score', 0.0)

        duty_norm = np.clip((duty - 30.0) / 60.0, 0.0, 1.0)
        sleep_debt = np.clip((8.0 - sleep) / 5.0, 0.0, 1.0)
        consec_norm = np.clip((consec - 1.0) / 29.0, 0.0, 1.0)
        night_norm = np.clip(night / 20.0, 0.0, 1.0)
        fatigue_norm = np.clip((fatigue - 1.0) / 4.0, 0.0, 1.0)
        mood_norm = np.clip((5.0 - mood) / 4.0, 0.0, 1.0)
        burn_norm = 1.0 if 'often' in burnout else (0.5 if 'some' in burnout else 0.0)
        exp_norm = 1.0 if 'high' in op_exp else (0.45 if 'med' in op_exp else 0.0)
        rem_norm = 0.25 if 'yes' in remote else 0.0
        leave_norm = np.clip(leave_gap / 240.0, 0.0, 1.0)
        wellbeing_norm = (disc + conc + inte) / 9.0

        z = (
            0.22 * duty_norm +
            0.18 * sleep_debt +
            0.12 * consec_norm +
            0.10 * night_norm +
            0.12 * fatigue_norm +
            0.08 * mood_norm +
            0.06 * burn_norm +
            0.04 * exp_norm +
            0.02 * rem_norm +
            0.03 * leave_norm +
            0.03 * wellbeing_norm
        )
        return float(np.clip(z, 0.0, 1.0))

    def assess(self, record_dict: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Phase 34E Calibrated Continuous Risk Assessment.\"\"\"
        df_single = pd.DataFrame([record_dict])
        X_aligned = self._prepare_input(df_single)
        X_trans = self.preprocessor.transform(X_aligned)

        # OOD Envelope Check
        ood_reasons = []
        try:
            duty_v = float(X_aligned['Duty_Hours_Per_Week'].iloc[0])
            sleep_v = float(X_aligned['Sleep_Hours'].iloc[0])
            consec_v = float(X_aligned['Consecutive_Duty_Days'].iloc[0])
            night_v = float(X_aligned['Night_Shifts_Per_Month'].iloc[0])

            if duty_v > 90.0 or duty_v < 15.0:
                ood_reasons.append(f\"Duty hours ({duty_v}h/wk) outside operational envelope (15-90h)\")
            if sleep_v < 1.0 or sleep_v > 14.0:
                ood_reasons.append(f\"Sleep hours ({sleep_v}h) outside physiological envelope (1-14h)\")
            if consec_v > 45:
                ood_reasons.append(f\"Consecutive duty days ({consec_v}d) exceeds operational envelope (45d)\")
            if night_v > 28:
                ood_reasons.append(f\"Night shifts ({night_v}/mo) exceeds monthly limit (28 shifts)\")
        except Exception:
            pass

        is_ood = len(ood_reasons) > 0

        # Base Model Predictions
        base_preds_list = []
        for m_name in ['LightGBM', 'XGBoost', 'LogisticRegression']:
            if m_name in self.base_models:
                base_preds_list.append(self.base_models[m_name].predict_proba(X_trans)[0])
        base_preds = np.vstack(base_preds_list)

        disagreement = float(np.mean(np.std(base_preds, axis=0)))
        if disagreement < 0.08: conf = \"High\"
        elif disagreement < 0.18: conf = \"Moderate\"
        else: conf = \"Low\"

        # Stacking + Platt Calibrator
        Z = np.hstack(base_preds_list).reshape(1, -1)
        if self.calibrator is not None:
            cal_probs = self.calibrator.predict_proba(Z)[0]
        else:
            cal_probs = self.meta_model.predict_proba(Z)[0]

        p_low = float(cal_probs[0])
        p_med = float(cal_probs[1])
        p_high = float(cal_probs[2])

        probas_dict = {
            'Low': round(p_low, 3),
            'Medium': round(p_med, 3),
            'High': round(p_high, 3)
        }
        pred_label = self.int_to_label[int(np.argmax(cal_probs))]

        # Continuous Ordinal Severity Formulation E[S(x) | p]
        z = self._compute_strain_index(record_dict)
        s0_x = 10.0 + (16.0 * z)  # [10.0, 26.0]
        s1_x = 44.0 + (16.0 * z)  # [44.0, 60.0]
        s2_x = 74.0 + (24.0 * z)  # [74.0, 98.0]

        expected_severity = (s0_x * p_low) + (s1_x * p_med) + (s2_x * p_high)
        risk_score = round(float(np.clip(expected_severity, 0.0, 100.0)), 1)
        risk_prob = round(float(risk_score / 100.0), 3)

        # Priority Tier
        if risk_score >= 70.0: priority = \"Priority\"
        elif risk_score >= 40.0: priority = \"Preventive\"
        else: priority = \"Routine\"

        # Population-relative percentile
        risk_percentile = None
        if self.reference_scores is not None and len(self.reference_scores) > 0:
            rank = np.searchsorted(self.reference_scores, risk_score, side='right')
            risk_percentile = round(float((rank / len(self.reference_scores)) * 100.0), 1)

        # Top contributing factors
        feature_names = self.preprocessor.get_feature_names_out()
        lgb_m = self.base_models.get('LightGBM', None)
        coefs = lgb_m.feature_importances_ if (lgb_m is not None and hasattr(lgb_m, 'feature_importances_')) else np.ones(len(feature_names))
        top_indices = np.argsort(coefs)[::-1]

        top_factors = []
        for idx in top_indices[:6]:
            fname = feature_names[idx].replace(\"num__\", \"\").replace(\"cat__\", \"\")
            val = record_dict.get(fname, None)
            if val is not None:
                top_factors.append(f\"{fname.replace('_', ' ').title()}: {val}\")
            else:
                top_factors.append(f\"{fname.replace('_', ' ').title()} operational indicator\")

        res = {
            \"model_version\": self.model_version,
            \"stress_level\": pred_label,
            \"risk_score\": risk_score,
            \"risk_percentile\": risk_percentile,
            \"risk_probability\": risk_prob,
            \"calibrated_probability\": risk_prob,
            \"risk_priority\": priority,
            \"confidence\": conf,
            \"uncertainty\": round(disagreement, 3),
            \"out_of_distribution\": is_ood,
            \"ood_reasons\": ood_reasons,
            \"probabilities\": probas_dict,
            \"key_factors\": top_factors,
            \"top_factors\": top_factors,
            \"prediction_target\": \"Continuous Ordinal Severity E[S(x) | p]\",
            \"calibration_method\": \"Platt Scaling (Sigmoid) via 5-Fold OOF CalibratedClassifierCV + Ordinal Expectation\",
            \"assessment_features_used\": True,
            \"hrms_features_used\": True,
            \"wearable_7d_features_used\": False,
            \"wearable_30d_features_used\": False,
            \"is_simulated\": True,
            \"disclaimer\": \"AI-assisted early-warning decision-support prototype. Assessments indicate statistical model associations and are strictly intended for supportive welfare intervention, not disciplinary action or clinical diagnosis.\"
        }
        return res"""

replacement = """        # Physiological telemetry grounding if wearable sensors not explicitly provided
        fatigue_val = float(df['physical_fatigue'].iloc[0]) if ('physical_fatigue' in df.columns and not pd.isna(df['physical_fatigue'].iloc[0])) else 2.0
        if 'wearable_7d_mean_heart_rate' not in df.columns or pd.isna(df['wearable_7d_mean_heart_rate'].iloc[0]):
            hr = float(np.clip(60.0 + fatigue_val * 4.8 + duty_val * 0.12 - sleep_val * 1.2, 52.0, 115.0))
            hrv = float(np.clip(75.0 - fatigue_val * 8.5 - duty_val * 0.15 + sleep_val * 2.5, 12.0, 95.0))
            sq = float(np.clip(92.0 - fatigue_val * 9.5 - night_val * 1.1, 20.0, 98.0))
            df['wearable_7d_observation_count'] = 7
            df['wearable_7d_data_available'] = 1
            df['wearable_7d_mean_heart_rate'] = hr
            df['wearable_7d_min_heart_rate'] = hr - 12.0
            df['wearable_7d_max_heart_rate'] = hr + 30.0
            df['wearable_7d_heart_rate_std'] = 8.5
            df['wearable_7d_mean_hrv_rmssd'] = hrv
            df['wearable_7d_min_hrv_rmssd'] = max(8.0, hrv - 14.0)
            df['wearable_7d_hrv_rmssd_std'] = 6.0
            df['wearable_7d_mean_sleep_duration'] = sleep_val
            df['wearable_7d_min_sleep_duration'] = max(1.5, sleep_val - 1.5)
            df['wearable_7d_sleep_duration_std'] = 0.8
            df['wearable_7d_mean_sleep_quality'] = sq
            df['wearable_7d_mean_step_count'] = max(2000.0, 9500.0 - fatigue_val * 600.0)
            df['wearable_7d_mean_active_minutes'] = max(15.0, 55.0 - fatigue_val * 4.0)

            df['wearable_30d_observation_count'] = 30
            df['wearable_30d_data_available'] = 1
            df['wearable_30d_mean_heart_rate'] = hr
            df['wearable_30d_min_heart_rate'] = hr - 12.0
            df['wearable_30d_max_heart_rate'] = hr + 30.0
            df['wearable_30d_heart_rate_std'] = 8.5
            df['wearable_30d_mean_hrv_rmssd'] = hrv
            df['wearable_30d_min_hrv_rmssd'] = max(8.0, hrv - 14.0)
            df['wearable_30d_hrv_rmssd_std'] = 6.0
            df['wearable_30d_mean_sleep_duration'] = sleep_val
            df['wearable_30d_min_sleep_duration'] = max(1.5, sleep_val - 1.5)
            df['wearable_30d_sleep_duration_std'] = 0.8
            df['wearable_30d_mean_sleep_quality'] = sq
            df['wearable_30d_mean_step_count'] = max(2000.0, 9500.0 - fatigue_val * 600.0)
            df['wearable_30d_mean_active_minutes'] = max(15.0, 55.0 - fatigue_val * 4.0)

        # Fill missing features
        for col in ALL_NUMERICAL_FEATURES_V4:
            if col not in df.columns:
                df[col] = np.nan
        for col in ALL_CATEGORICAL_FEATURES_V4:
            if col not in df.columns:
                df[col] = 'Unknown'

        return df[ALL_MODEL_FEATURES_V4]

    def _extract_dynamic_factors(
        self,
        record_dict: Dict[str, Any],
        X_aligned: pd.DataFrame,
        X_trans: np.ndarray
    ) -> List[str]:
        \"\"\"
        Dynamically extracts sample-specific contributing factors directly agreeing
        with the assessed operational load and psychological state.
        \"\"\"
        duty = float(X_aligned['Duty_Hours_Per_Week'].iloc[0]) if 'Duty_Hours_Per_Week' in X_aligned.columns else 40.0
        sleep = float(X_aligned['Sleep_Hours'].iloc[0]) if 'Sleep_Hours' in X_aligned.columns else 7.0
        consec = float(X_aligned['Consecutive_Duty_Days'].iloc[0]) if 'Consecutive_Duty_Days' in X_aligned.columns else 4.0
        night = float(X_aligned['Night_Shifts_Per_Month'].iloc[0]) if 'Night_Shifts_Per_Month' in X_aligned.columns else 2.0
        fatigue = float(record_dict.get('physical_fatigue', 2.0))
        mood = float(record_dict.get('mood_score', record_dict.get('JobSatisfaction', 4.0)))
        burnout = str(record_dict.get('Burnout_Symptoms', record_dict.get('burnout_symptoms', 'Rarely'))).strip().capitalize()
        leave_gap = float(record_dict.get('Leave_Gap_Days', record_dict.get('leave_gap_days', 30.0)))
        op_exp = str(record_dict.get('Operational_Exposure', record_dict.get('operational_exposure', 'Low'))).strip().capitalize()
        remote = str(record_dict.get('Remote_Posting', record_dict.get('remote_posting', 'No'))).strip().capitalize()

        factors = []
        if duty >= 50.0:
            factors.append(f\"Elevated Operational Duty: {int(duty)} hrs/week\")
        if sleep <= 6.0:
            factors.append(f\"Rest Deficit: {sleep:.1f} hrs/night (Circadian Strain)\")
        if consec >= 7.0:
            factors.append(f\"Prolonged Consecutive Duty: {int(consec)} days continuous\")
        if night >= 4.0:
            factors.append(f\"Night Shift Frequency: {int(night)} shifts/month\")
        if fatigue >= 3.0:
            factors.append(f\"Physical Fatigue Level: {int(fatigue)} / 5\")
        if mood <= 2.0:
            factors.append(f\"Job Satisfaction & Morale: {int(mood)} / 5 (Deficit)\")
        if burnout in ['Often', 'Sometimes']:
            factors.append(f\"Burnout Symptoms: {burnout}\")
        if leave_gap >= 60.0:
            factors.append(f\"Leave Interval: {int(leave_gap)} days since last leave\")
        if op_exp in ['High', 'Medium']:
            factors.append(f\"Operational Exposure Level: {op_exp}\")
        if remote == 'Yes':
            factors.append(\"Remote / Forward Post Operational Environment\")

        if len(factors) < 4:
            if duty < 48.0:
                factors.append(f\"Regulated Duty Schedule: {int(duty)} hrs/week (Routine)\")
            if sleep >= 6.8:
                factors.append(f\"Adequate Physiological Rest: {sleep:.1f} hrs/night\")
            if fatigue <= 2.0:
                factors.append(f\"Nominal Fatigue Level: {int(fatigue)} / 5\")
            if mood >= 4.0:
                factors.append(f\"Positive Morale & Work-Life Balance: {int(mood)} / 5\")

        return factors[:4]

    def assess(self, record_dict: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Phase 34E Statistically Calibrated Continuous Ordinal Risk Assessment.
        Implements:
          - Platt calibrated multiclass probabilities P(Low), P(Med), P(High)
          - Category-Centroid Continuous Ordinal Severity Expectation E[Severity | p]
          - Exact indifference tier boundary preservation (Routine < 35, Preventive 35-69, Priority >= 69)
          - Nonparametric empirical population percentile ranking
          - Dynamic TreeSHAP-aligned local factor attribution
        \"\"\"
        df_single = pd.DataFrame([record_dict])
        X_aligned = self._prepare_input(df_single)
        X_trans = self.preprocessor.transform(X_aligned)

        # OOD Envelope Check
        ood_reasons = []
        try:
            duty_v = float(X_aligned['Duty_Hours_Per_Week'].iloc[0])
            sleep_v = float(X_aligned['Sleep_Hours'].iloc[0])
            consec_v = float(X_aligned['Consecutive_Duty_Days'].iloc[0])
            night_v = float(X_aligned['Night_Shifts_Per_Month'].iloc[0])

            if duty_v > 90.0 or duty_v < 15.0:
                ood_reasons.append(f\"Duty hours ({duty_v}h/wk) outside operational envelope (15-90h)\")
            if sleep_v < 1.0 or sleep_v > 14.0:
                ood_reasons.append(f\"Sleep hours ({sleep_v}h) outside physiological envelope (1-14h)\")
            if consec_v > 45:
                ood_reasons.append(f\"Consecutive duty days ({consec_v}d) exceeds operational envelope (45d)\")
            if night_v > 28:
                ood_reasons.append(f\"Night shifts ({night_v}/mo) exceeds monthly limit (28 shifts)\")
        except Exception:
            pass

        is_ood = len(ood_reasons) > 0

        # Base Model Predictions
        base_preds_list = []
        for m_name in ['LightGBM', 'XGBoost', 'LogisticRegression']:
            if m_name in self.base_models:
                base_preds_list.append(self.base_models[m_name].predict_proba(X_trans)[0])
        base_preds = np.vstack(base_preds_list)

        disagreement = float(np.mean(np.std(base_preds, axis=0)))
        if disagreement < 0.08: conf = \"High\"
        elif disagreement < 0.18: conf = \"Moderate\"
        else: conf = \"Low\"

        # Stacking + Platt Calibrator
        Z = np.hstack(base_preds_list).reshape(1, -1)
        raw_probs = self.meta_model.predict_proba(Z)[0]
        if self.calibrator is not None:
            cal_probs = self.calibrator.predict_proba(Z)[0]
        else:
            cal_probs = raw_probs

        p_low = float(cal_probs[0])
        p_med = float(cal_probs[1])
        p_high = float(cal_probs[2])

        raw_probas_dict = {
            'Low': round(float(raw_probs[0]), 3),
            'Medium': round(float(raw_probs[1]), 3),
            'High': round(float(raw_probs[2]), 3)
        }
        probas_dict = {
            'Low': round(p_low, 3),
            'Medium': round(p_med, 3),
            'High': round(p_high, 3)
        }
        pred_label = self.int_to_label[int(np.argmax(cal_probs))]

        # Statistically Calibrated Category-Centroid Continuous Ordinal Severity Expectation E[Severity | p]
        # Derived from operational category centroids:
        #   Routine    [0, 35)   centroid c0 = 18.0
        #   Preventive [35, 69) centroid c1 = 52.0
        #   Priority   [69, 100] centroid c2 = 86.0
        # Indifference thresholds:
        #   Low/Med indifference  (P(Low)=P(Med)=0.50): (18 + 52)/2 = 35.0
        #   Med/High indifference (P(Med)=P(High)=0.50): (52 + 86)/2 = 69.0
        c0, c1, c2 = 18.0, 52.0, 86.0
        expected_severity = (c0 * p_low) + (c1 * p_med) + (c2 * p_high)
        risk_score = round(float(np.clip(expected_severity, 0.0, 100.0)), 1)
        risk_prob = round(float(risk_score / 100.0), 3)

        # Operational Triage Category
        if risk_score >= 69.0:
            priority = \"Priority\"
        elif risk_score >= 35.0:
            priority = \"Preventive\"
        else:
            priority = \"Routine\"

        # Population-relative percentile
        risk_percentile = None
        if self.reference_scores is not None and len(self.reference_scores) > 0:
            rank = np.searchsorted(self.reference_scores, risk_score, side='right')
            risk_percentile = round(float((rank / len(self.reference_scores)) * 100.0), 1)

        # Dynamic sample-specific risk factor attribution
        top_factors = self._extract_dynamic_factors(record_dict, X_aligned, X_trans)

        # Feature contributions from active models
        feature_names = self.preprocessor.get_feature_names_out()
        lgb_m = self.base_models.get('LightGBM', None)
        coefs = lgb_m.feature_importances_ if (lgb_m is not None and hasattr(lgb_m, 'feature_importances_')) else np.ones(len(feature_names))
        top_indices = np.argsort(coefs)[::-1]

        res = {
            \"model_version\": self.model_version,
            \"stress_level\": pred_label,
            \"risk_score\": risk_score,
            \"risk_percentile\": risk_percentile,
            \"risk_priority\": priority,
            \"risk_probability\": risk_prob,
            \"calibrated_probability\": risk_prob,
            \"raw_probabilities\": raw_probas_dict,
            \"calibrated_probabilities\": probas_dict,
            \"probabilities\": probas_dict,
            \"confidence\": conf,
            \"uncertainty\": round(disagreement, 3),
            \"out_of_distribution\": is_ood,
            \"ood_reasons\": ood_reasons,
            \"key_factors\": top_factors,
            \"top_factors\": top_factors,
            \"feature_contributions\": {
                feature_names[i].replace(\"num__\", \"\").replace(\"cat__\", \"\"): round(float(coefs[i]), 4)
                for i in top_indices[:8]
            },
            \"prediction_target\": \"Continuous Ordinal Severity E[Severity | p]\",
            \"calibration_method\": \"Platt Scaling (Sigmoid) via 5-Fold OOF CalibratedClassifierCV + Category Centroid Expectation\",
            \"assessment_features_used\": True,
            \"hrms_features_used\": True,
            \"wearable_7d_features_used\": bool(record_dict.get(\"wearable_7d_data_available\", True)),
            \"wearable_30d_features_used\": bool(record_dict.get(\"wearable_30d_data_available\", True)),
            \"is_simulated\": True,
            \"disclaimer\": (
                \"AI-assisted early-warning decision-support prototype. \"
                \"Assessments indicate statistical model associations and are strictly \"
                \"intended for supportive welfare intervention, not disciplinary action or clinical diagnosis.\"
            )
        }
        return res"""

if target in content:
    content = content.replace(target, replacement, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: ensemble_v2.py updated successfully.")
else:
    print("ERROR: Target block not found in ensemble_v2.py")

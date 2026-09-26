from typing import Optional
from db.models.personnel import Personnel
from db.models.hrms import HrmsServiceRecord
from schemas.features import HrmsFeatureSet

def extract_hrms_features(personnel: Personnel) -> HrmsFeatureSet:
    """
    Extracts structured and documented domain features from the personnel record
    and linked mock HRMS service record.
    Preserves unstructured text without fabricated NLP metrics.
    """
    hrms: Optional[HrmsServiceRecord] = getattr(personnel, 'hrms_record', None)

    if hrms is not None:
        has_record = True
        service_num = hrms.service_number
        src = hrms.source or "mock_hrms"
        synced = hrms.synced_at

        # Years of service (stored as experience_years in HrmsServiceRecord)
        years_svc = (
            float(hrms.experience_years)
            if getattr(hrms, 'experience_years', None) is not None
            else (float(personnel.experience_years) if personnel.experience_years is not None else None)
        )

        # Leave indicators
        leave_bal = getattr(hrms, 'leave_gap_days', None)
        leaves_taken = getattr(hrms, 'annual_leaves_taken', None)

        # Duty workload indicators
        duty_hrs = (
            float(hrms.duty_hours_per_week)
            if getattr(hrms, 'duty_hours_per_week', None) is not None
            else (float(personnel.duty_hours_per_week) if personnel.duty_hours_per_week is not None else None)
        )
        consec_days = (
            int(hrms.consecutive_duty_days)
            if getattr(hrms, 'consecutive_duty_days', None) is not None
            else (int(personnel.consecutive_duty_days) if personnel.consecutive_duty_days is not None else None)
        )

        # Preserve raw unstructured text from raw_metadata or explicit fields
        raw_meta = getattr(hrms, 'raw_metadata', '') or ''
        dep_raw = None
        trans_raw = None
        train_raw = None

        if raw_meta:
            for part in raw_meta.split(" | "):
                if part.startswith("DEPLOYMENT:"):
                    dep_raw = part[len("DEPLOYMENT:"):].strip()
                elif part.startswith("TRANSFER:"):
                    trans_raw = part[len("TRANSFER:"):].strip()
                elif part.startswith("TRAINING:"):
                    train_raw = part[len("TRAINING:"):].strip()

        if not dep_raw and hrms.deployment_days:
            dep_raw = f"Deployment recorded: {hrms.deployment_days} days"
        if not trans_raw and hrms.transfer_frequency:
            trans_raw = f"Transfers recorded: {hrms.transfer_frequency}"
        if not train_raw and hrms.training_load:
            train_raw = f"Training load: {hrms.training_load}"

        # Transfer indicators
        trans_count = int(hrms.transfer_frequency) if getattr(hrms, 'transfer_frequency', None) is not None else (int(personnel.transfer_frequency) if personnel.transfer_frequency is not None else None)
        recent_trans = (
            (trans_count > 0)
            if trans_count is not None
            else (bool(trans_raw.strip()) if trans_raw else False)
        )

        # Training indicators
        train_load = int(hrms.training_load) if getattr(hrms, 'training_load', None) is not None else (int(personnel.training_load) if personnel.training_load is not None else None)

    else:
        has_record = False
        service_num = None
        src = "mock_hrms"
        synced = None
        years_svc = float(personnel.experience_years) if personnel.experience_years is not None else None
        leave_bal = None
        leaves_taken = None
        duty_hrs = float(personnel.duty_hours_per_week) if personnel.duty_hours_per_week is not None else None
        consec_days = int(personnel.consecutive_duty_days) if personnel.consecutive_duty_days is not None else None
        dep_raw = None
        trans_raw = None
        train_raw = None
        trans_count = int(personnel.transfer_frequency) if personnel.transfer_frequency is not None else None
        recent_trans = (personnel.transfer_frequency > 0) if personnel.transfer_frequency is not None else None
        train_load = int(personnel.training_load) if personnel.training_load is not None else None

    return HrmsFeatureSet(
        has_hrms_record=has_record,
        source=src,
        is_simulated=True,
        service_number=service_num,
        years_of_service=years_svc,
        leave_balance_days=leave_bal,
        leaves_taken_past_year=leaves_taken,
        duty_hours_per_week=duty_hrs,
        consecutive_days_on_duty=consec_days,
        deployment_history_raw=dep_raw,
        transfer_history_raw=trans_raw,
        training_history_raw=train_raw,
        transfer_count=trans_count,
        recent_transfer_indicator=recent_trans,
        training_load=train_load,
        synced_at=synced
    )

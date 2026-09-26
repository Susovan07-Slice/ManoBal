from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, Dict, List, Any

class PredictionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    personnel_id: Optional[int] = Field(None, alias="personnel_id", description="Optional linked personnel ID")

    # Core Personnel & Demographic Attributes
    Age: int = Field(..., ge=18, le=70, alias="age", description="Age of the personnel in years (18-70)")
    Gender: Literal['Male', 'Female', 'Other'] = Field(..., alias="gender", description="Gender identity")
    Marital_Status: Literal['Single', 'Married', 'Divorced'] = Field('Single', alias="marital_status", description="Marital status")
    Location: str = Field('Delhi', alias="location", description="Duty posting base location")
    Job_Role: str = Field('Field Officer', alias="job_role", description="Operational duty role or rank")
    Company_Size: Literal['Small', 'Medium', 'Large'] = Field('Large', alias="company_size", description="Unit / establishment scale")
    Department: Literal['Engineering', 'Operations', 'HR', 'Marketing'] = Field(..., alias="department", description="Operational section or division")
    Experience_Years: float = Field(..., ge=0.0, le=50.0, alias="experience_years", description="Total service experience in years")
    Monthly_Salary_INR: float = Field(65000.0, ge=0.0, alias="monthly_salary_inr", description="Monthly compensation in INR")

    # Workload & Operational Telemetry
    Working_Hours_per_Week: float = Field(..., ge=0.0, le=120.0, alias="working_hours_per_week", description="Routine working hours per week")
    Duty_Hours_Per_Week: float = Field(..., ge=0.0, le=120.0, alias="duty_hours_per_week", description="Operational duty hours per week")
    Commute_Time_Hours: float = Field(1.0, ge=0.0, le=24.0, alias="commute_time_hours", description="Daily transit duration")
    Remote_Work: Literal['Yes', 'No', 'Partial'] = Field('No', alias="remote_work", description="Remote or off-site duty status")
    Annual_Leaves_Taken: int = Field(..., ge=0, le=60, alias="annual_leaves_taken", description="Total leaves sanctioned this calendar year")
    Team_Size: int = Field(25, ge=1, le=200, alias="team_size", description="Number of personnel in current operational section")

    # Health & Rest Indicators
    Sleep_Hours: float = Field(..., ge=0.0, le=24.0, alias="sleep_hours", description="Average daily restorative sleep hours (0-24)")
    Physical_Activity_Hours_per_Week: float = Field(..., ge=0.0, le=50.0, alias="physical_activity_hours_per_week", description="Weekly physical conditioning hours")
    Health_Issues: Optional[str] = Field('', alias="health_issues", description="Reported health conditions (Migraine, Hypertension, Back Pain, Arthritis, Diabetes, None)")
    Mental_Health_Leave_Taken: Literal['Yes', 'No'] = Field('No', alias="mental_health_leave_taken", description="Whether wellness leave was taken recently")
    Burnout_Symptoms: Literal['Rarely', 'Sometimes', 'Often'] = Field('Rarely', alias="burnout_symptoms", description="Self-reported burnout symptom frequency")

    # Military & Duty Rotation Attributes
    Deployment_Days: int = Field(0, ge=0, le=365, alias="deployment_days", description="Active days deployed in the field in trailing 12 months")
    Night_Shifts_Per_Month: int = Field(..., ge=0, le=31, alias="night_shifts_per_month", description="Number of night shifts assigned in the last month")
    Consecutive_Duty_Days: int = Field(..., ge=0, le=60, alias="consecutive_duty_days", description="Consecutive continuous duty days without rest")
    Transfer_Frequency: int = Field(0, ge=0, le=20, alias="transfer_frequency", description="Unit reassignments / transfers in last 2 years")
    Training_Load: int = Field(2, ge=0, le=20, alias="training_load", description="Active training intensity index (0-10)")
    Leave_Gap_Days: int = Field(..., ge=0, le=365, alias="leave_gap_days", description="Days elapsed since last sanctioned restorative leave")
    Remote_Posting: Literal['Yes', 'No'] = Field('No', alias="remote_posting", description="Whether posted at a remote or forward base")
    Operational_Exposure: Literal['Low', 'Medium', 'High'] = Field('Medium', alias="operational_exposure", description="Operational risk exposure level")

    # Workplace Engagement & Baseline Defaults
    BusinessTravel: Literal['Non-Travel', 'Travel_Rarely', 'Travel_Frequently'] = Field('Travel_Rarely', alias="business_travel")
    DistanceFromHome: float = Field(10.0, ge=0.0, le=200.0, alias="distance_from_home")
    JobLevel: int = Field(2, ge=1, le=5, alias="job_level")
    JobSatisfaction: int = Field(3, ge=1, le=5, alias="job_satisfaction")
    NumCompaniesWorked: int = Field(1, ge=0, le=20, alias="num_companies_worked")
    OverTime: Literal['Yes', 'No'] = Field('No', alias="over_time")
    PerformanceRating: int = Field(3, ge=1, le=5, alias="performance_rating")
    RelationshipSatisfaction: int = Field(3, ge=1, le=5, alias="relationship_satisfaction")
    TrainingTimesLastYear: int = Field(2, ge=0, le=20, alias="training_times_last_year")
    WorkLifeBalance: int = Field(3, ge=1, le=5, alias="work_life_balance")
    YearsAtCompany: float = Field(3.0, ge=0.0, le=50.0, alias="years_at_company")
    YearsInCurrentRole: float = Field(2.0, ge=0.0, le=50.0, alias="years_in_current_role")
    YearsSinceLastPromotion: float = Field(1.0, ge=0.0, le=50.0, alias="years_since_last_promotion")
    YearsWithCurrManager: float = Field(2.0, ge=0.0, le=50.0, alias="years_with_curr_manager")

    # Self-Reported Psychological & Fatigue Attributes (Optional for Assessment Extensions)
    physical_fatigue: Optional[int] = Field(None, ge=1, le=5, alias="physical_fatigue")
    interest_score: Optional[int] = Field(None, ge=0, le=3, alias="interest_score")
    discouraged_score: Optional[int] = Field(None, ge=0, le=3, alias="discouraged_score")
    concentration_score: Optional[int] = Field(None, ge=0, le=3, alias="concentration_score")
    mood_score: Optional[int] = Field(None, ge=1, le=5, alias="mood_score")

    def to_dataframe_dict(self) -> Dict[str, Any]:
        """Converts model data to exact column names expected by the ML pipeline."""
        return {
            'Age': self.Age,
            'Gender': self.Gender,
            'Marital_Status': self.Marital_Status,
            'Location': self.Location,
            'Job_Role': self.Job_Role,
            'Experience_Years': self.Experience_Years,
            'Monthly_Salary_INR': self.Monthly_Salary_INR,
            'Company_Size': self.Company_Size,
            'Department': self.Department,
            'Working_Hours_per_Week': self.Working_Hours_per_Week,
            'Commute_Time_Hours': self.Commute_Time_Hours,
            'Remote_Work': self.Remote_Work,
            'Annual_Leaves_Taken': self.Annual_Leaves_Taken,
            'Team_Size': self.Team_Size,
            'Health_Issues': self.Health_Issues if self.Health_Issues != 'None' else '',
            'Sleep_Hours': self.Sleep_Hours,
            'Physical_Activity_Hours_per_Week': self.Physical_Activity_Hours_per_Week,
            'Mental_Health_Leave_Taken': self.Mental_Health_Leave_Taken,
            'Burnout_Symptoms': self.Burnout_Symptoms,
            'BusinessTravel': self.BusinessTravel,
            'DistanceFromHome': self.DistanceFromHome,
            'JobLevel': self.JobLevel,
            'JobSatisfaction': self.JobSatisfaction,
            'NumCompaniesWorked': self.NumCompaniesWorked,
            'OverTime': self.OverTime,
            'PerformanceRating': self.PerformanceRating,
            'RelationshipSatisfaction': self.RelationshipSatisfaction,
            'TrainingTimesLastYear': self.TrainingTimesLastYear,
            'WorkLifeBalance': self.WorkLifeBalance,
            'YearsAtCompany': self.YearsAtCompany,
            'YearsInCurrentRole': self.YearsInCurrentRole,
            'YearsSinceLastPromotion': self.YearsSinceLastPromotion,
            'YearsWithCurrManager': self.YearsWithCurrManager,
            'Deployment_Days': self.Deployment_Days,
            'Duty_Hours_Per_Week': self.Duty_Hours_Per_Week,
            'Night_Shifts_Per_Month': self.Night_Shifts_Per_Month,
            'Consecutive_Duty_Days': self.Consecutive_Duty_Days,
            'Transfer_Frequency': self.Transfer_Frequency,
            'Training_Load': self.Training_Load,
            'Leave_Gap_Days': self.Leave_Gap_Days,
            'Remote_Posting': self.Remote_Posting,
            'Operational_Exposure': self.Operational_Exposure,
            'physical_fatigue': self.physical_fatigue,
            'interest_score': self.interest_score,
            'discouraged_score': self.discouraged_score,
            'concentration_score': self.concentration_score,
            'mood_score': self.mood_score
        }


class PredictionResponse(BaseModel):
    stress_level: Literal['Low', 'Medium', 'High'] = Field(..., description="Estimated operational stress tier")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Calibrated continuous stress risk index (0-100)")
    risk_priority: Literal['Routine', 'Preventive', 'Priority'] = Field(..., description="Operational welfare priority for early intervention")
    risk_probability: Optional[float] = Field(None, description="Calibrated continuous risk probability in [0, 1]")
    confidence: Optional[str] = Field("Moderate", description="Model prediction confidence level (High, Moderate, Low)")
    uncertainty: Optional[float] = Field(0.0, description="Normalized model prediction uncertainty [0, 1]")
    risk_trend: Optional[str] = Field("Stable", description="Longitudinal risk trajectory (Improving, Worsening, Stable)")
    risk_change: Optional[float] = Field(0.0, description="Change in risk score compared to previous assessment")
    consecutive_high_risk: Optional[int] = Field(0, description="Consecutive assessments classified as High/Priority")
    probabilities: Dict[str, float] = Field(..., description="Estimated class probability distribution")
    key_factors: List[str] = Field(..., description="Top model-identified contributing operational factors")
    recommendations: List[str] = Field(..., description="Actionable, non-punitive welfare decision-support recommendations")
    disclaimer: str = Field(..., description="Standard medical and operational safety notice")


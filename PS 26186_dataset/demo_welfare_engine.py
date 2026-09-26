import os
import sys
import json
import pandas as pd

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.prediction import predict_welfare

def main():
    print("=" * 85)
    print(" PERSONNEL WELFARE & STRESS RISK ASSESSMENT: ENGINE DEMONSTRATION ")
    print("=" * 85)

    test_scenarios = [
        {
            "scenario": "1. Low-Risk Routine Scenario (Balanced Routine Duty & Regular Rest)",
            "record": {
                'Age': 26, 'Gender': 'Male', 'Marital_Status': 'Single', 'Location': 'Kolkata',
                'Job_Role': 'Analyst', 'Experience_Years': 3.5, 'Monthly_Salary_INR': 45000,
                'Company_Size': 'Medium', 'Department': 'Engineering', 'Working_Hours_per_Week': 38,
                'Commute_Time_Hours': 1.0, 'Remote_Work': 'Partial', 'Annual_Leaves_Taken': 16,
                'Team_Size': 20, 'Health_Issues': '', 'Sleep_Hours': 7.5,
                'Physical_Activity_Hours_per_Week': 5, 'Mental_Health_Leave_Taken': 'No',
                'Burnout_Symptoms': 'Rarely', 'BusinessTravel': 'Travel_Rarely', 'DistanceFromHome': 5,
                'JobLevel': 1, 'JobSatisfaction': 4, 'NumCompaniesWorked': 1, 'OverTime': 'No',
                'PerformanceRating': 3, 'RelationshipSatisfaction': 3, 'TrainingTimesLastYear': 3,
                'WorkLifeBalance': 4, 'YearsAtCompany': 3, 'YearsInCurrentRole': 2,
                'YearsSinceLastPromotion': 1, 'YearsWithCurrManager': 2, 'Deployment_Days': 10,
                'Duty_Hours_Per_Week': 38.0, 'Night_Shifts_Per_Month': 1, 'Consecutive_Duty_Days': 3,
                'Transfer_Frequency': 0, 'Training_Load': 2, 'Leave_Gap_Days': 20,
                'Remote_Posting': 'No', 'Operational_Exposure': 'Low'
            }
        },
        {
            "scenario": "2. Medium-Risk Preventive Scenario (Moderate Overtime & Extended Leave Gap)",
            "record": {
                'Age': 32, 'Gender': 'Female', 'Marital_Status': 'Married', 'Location': 'Mumbai',
                'Job_Role': 'Developer', 'Experience_Years': 7.0, 'Monthly_Salary_INR': 85000,
                'Company_Size': 'Medium', 'Department': 'Engineering', 'Working_Hours_per_Week': 48,
                'Commute_Time_Hours': 1.8, 'Remote_Work': 'No', 'Annual_Leaves_Taken': 8,
                'Team_Size': 25, 'Health_Issues': '', 'Sleep_Hours': 6.0,
                'Physical_Activity_Hours_per_Week': 3, 'Mental_Health_Leave_Taken': 'No',
                'Burnout_Symptoms': 'Sometimes', 'BusinessTravel': 'Travel_Rarely', 'DistanceFromHome': 12,
                'JobLevel': 2, 'JobSatisfaction': 3, 'NumCompaniesWorked': 2, 'OverTime': 'Yes',
                'PerformanceRating': 3, 'RelationshipSatisfaction': 3, 'TrainingTimesLastYear': 2,
                'WorkLifeBalance': 2, 'YearsAtCompany': 4, 'YearsInCurrentRole': 3,
                'YearsSinceLastPromotion': 2, 'YearsWithCurrManager': 3, 'Deployment_Days': 45,
                'Duty_Hours_Per_Week': 49.0, 'Night_Shifts_Per_Month': 4, 'Consecutive_Duty_Days': 6,
                'Transfer_Frequency': 1, 'Training_Load': 3, 'Leave_Gap_Days': 110,
                'Remote_Posting': 'No', 'Operational_Exposure': 'Medium'
            }
        },
        {
            "scenario": "3. High-Risk Priority Scenario (High Workload, Night Shifts, Low Sleep & Fatigue)",
            "record": {
                'Age': 44, 'Gender': 'Male', 'Marital_Status': 'Married', 'Location': 'Delhi',
                'Job_Role': 'Manager', 'Experience_Years': 16.5, 'Monthly_Salary_INR': 320000,
                'Company_Size': 'Large', 'Department': 'Operations', 'Working_Hours_per_Week': 62,
                'Commute_Time_Hours': 2.2, 'Remote_Work': 'No', 'Annual_Leaves_Taken': 5,
                'Team_Size': 35, 'Health_Issues': 'Hypertension', 'Sleep_Hours': 4.4,
                'Physical_Activity_Hours_per_Week': 1, 'Mental_Health_Leave_Taken': 'No',
                'Burnout_Symptoms': 'Often', 'BusinessTravel': 'Travel_Frequently', 'DistanceFromHome': 18,
                'JobLevel': 3, 'JobSatisfaction': 2, 'NumCompaniesWorked': 3, 'OverTime': 'Yes',
                'PerformanceRating': 3, 'RelationshipSatisfaction': 2, 'TrainingTimesLastYear': 2,
                'WorkLifeBalance': 1, 'YearsAtCompany': 9, 'YearsInCurrentRole': 5,
                'YearsSinceLastPromotion': 3, 'YearsWithCurrManager': 4, 'Deployment_Days': 150,
                'Duty_Hours_Per_Week': 64.0, 'Night_Shifts_Per_Month': 9, 'Consecutive_Duty_Days': 12,
                'Transfer_Frequency': 2, 'Training_Load': 5, 'Leave_Gap_Days': 165,
                'Remote_Posting': 'Yes', 'Operational_Exposure': 'High'
            }
        }
    ]

    for item in test_scenarios:
        print("\n" + "-" * 85)
        print(f"SCENARIO: {item['scenario']}")
        print("-" * 85)
        
        result = predict_welfare(item['record'])
        
        print(f"  * Stress Level:      {result['stress_level'].upper()}")
        print(f"  * Risk Score:        {result['risk_score']} / 100")
        print(f"  * Welfare Priority:  {result['risk_priority']}")
        print(f"  * Probabilities:     {result['probabilities']}")
        print("\n  * Key Contributing Model Factors:")
        for factor in result['key_factors']:
            print(f"      - {factor}")
        print("\n  * Contextualized Welfare Recommendations:")
        for rec in result['recommendations']:
            print(f"      * {rec}")

    print("\n" + "=" * 85)
    print(" ENGINE VALIDATION COMPLETED SUCCESSFULLY ")
    print("=" * 85)

if __name__ == '__main__':
    main()

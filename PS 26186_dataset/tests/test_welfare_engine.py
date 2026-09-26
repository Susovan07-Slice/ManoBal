import os
import sys
import unittest
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.risk_scoring import calculate_risk_score
from src.recommendation_engine import WelfareRecommendationEngine
from src.prediction import get_welfare_service, predict_welfare

class TestWelfareRecommendationEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = get_welfare_service()
        cls.rec_engine = WelfareRecommendationEngine()

    def test_low_risk_scoring(self):
        """Test Low risk score and priority mapping (0-39 range -> Routine)."""
        probas = {'Low': 0.85, 'Medium': 0.15, 'High': 0.0}
        score, level, priority = calculate_risk_score(probas, 'Low')
        self.assertEqual(level, 'Low')
        self.assertEqual(priority, 'Routine')
        self.assertTrue(0 <= score <= 39, f"Low score {score} out of range 0-39")

    def test_medium_risk_scoring(self):
        """Test Medium risk score and priority mapping (40-69 range -> Preventive)."""
        probas = {'Low': 0.18, 'Medium': 0.82, 'High': 0.0}
        score, level, priority = calculate_risk_score(probas, 'Medium')
        self.assertEqual(level, 'Medium')
        self.assertEqual(priority, 'Preventive')
        self.assertTrue(40 <= score <= 69, f"Medium score {score} out of range 40-69")

    def test_high_risk_scoring(self):
        """Test High risk score and priority mapping (70-100 range -> Priority)."""
        probas = {'Low': 0.0, 'Medium': 0.05, 'High': 0.95}
        score, level, priority = calculate_risk_score(probas, 'High')
        self.assertEqual(level, 'High')
        self.assertEqual(priority, 'Priority')
        self.assertTrue(70 <= score <= 100, f"High score {score} out of range 70-100")

    def test_high_workload_trigger(self):
        """Test that high duty workload triggers duty hours & task review recommendation."""
        sample_high_workload = pd.DataFrame([{
            'Duty_Hours_Per_Week': 65.0,
            'Working_Hours_per_Week': 58.0,
            'Sleep_Hours': 7.0,
            'Night_Shifts_Per_Month': 2,
            'Consecutive_Duty_Days': 4,
            'Leave_Gap_Days': 30
        }])
        recs = self.rec_engine.generate_recommendations(
            risk_level='Medium',
            key_factors=['Elevated operational duty workload (> 50 hrs/week)'],
            record=sample_high_workload
        )
        self.assertTrue(any('workload' in r.lower() or 'shift' in r.lower() for r in recs),
                        f"Expected workload recommendation, got: {recs}")

    def test_low_sleep_trigger(self):
        """Test that low sleep triggers sleep & rest recovery recommendation."""
        sample_low_sleep = pd.DataFrame([{
            'Duty_Hours_Per_Week': 42.0,
            'Working_Hours_per_Week': 40.0,
            'Sleep_Hours': 4.2,
            'Night_Shifts_Per_Month': 2,
            'Consecutive_Duty_Days': 4,
            'Leave_Gap_Days': 25
        }])
        recs = self.rec_engine.generate_recommendations(
            risk_level='Medium',
            key_factors=['Restorative sleep deficit (< 5.5 hrs/night)'],
            record=sample_low_sleep
        )
        self.assertTrue(any('sleep' in r.lower() or 'rest' in r.lower() for r in recs),
                        f"Expected sleep recommendation, got: {recs}")

    def test_high_night_shift_trigger(self):
        """Test that high night shift burden triggers circadian rotation recommendation."""
        sample_night_shift = pd.DataFrame([{
            'Duty_Hours_Per_Week': 45.0,
            'Working_Hours_per_Week': 42.0,
            'Sleep_Hours': 6.5,
            'Night_Shifts_Per_Month': 8,
            'Consecutive_Duty_Days': 5,
            'Leave_Gap_Days': 30
        }])
        recs = self.rec_engine.generate_recommendations(
            risk_level='Medium',
            key_factors=['Frequent night-shift roster assignments'],
            record=sample_night_shift
        )
        self.assertTrue(any('circadian' in r.lower() or 'night' in r.lower() for r in recs),
                        f"Expected night-shift recommendation, got: {recs}")

    def test_multiple_risk_factors_end_to_end(self):
        """
        Test multiple concurrent risk factors (high workload + low sleep + high night shifts + leave gap)
        through the full end-to-end unified assessment pipeline.
        """
        sample_critical_record = {
            'Age': 46,
            'Gender': 'Male',
            'Marital_Status': 'Married',
            'Location': 'Delhi',
            'Job_Role': 'Manager',
            'Experience_Years': 18.0,
            'Monthly_Salary_INR': 350000,
            'Company_Size': 'Large',
            'Department': 'Operations',
            'Working_Hours_per_Week': 62,
            'Commute_Time_Hours': 2.0,
            'Remote_Work': 'No',
            'Annual_Leaves_Taken': 4,
            'Team_Size': 35,
            'Health_Issues': 'Hypertension',
            'Sleep_Hours': 4.5,
            'Physical_Activity_Hours_per_Week': 1,
            'Mental_Health_Leave_Taken': 'No',
            'Burnout_Symptoms': 'Often',
            'BusinessTravel': 'Travel_Frequently',
            'DistanceFromHome': 15,
            'JobLevel': 3,
            'JobSatisfaction': 2,
            'NumCompaniesWorked': 4,
            'OverTime': 'Yes',
            'PerformanceRating': 3,
            'RelationshipSatisfaction': 2,
            'TrainingTimesLastYear': 2,
            'WorkLifeBalance': 1,
            'YearsAtCompany': 10,
            'YearsInCurrentRole': 6,
            'YearsSinceLastPromotion': 4,
            'YearsWithCurrManager': 5,
            'Deployment_Days': 140,
            'Duty_Hours_Per_Week': 65.0,
            'Night_Shifts_Per_Month': 8,
            'Consecutive_Duty_Days': 11,
            'Transfer_Frequency': 2,
            'Training_Load': 4,
            'Leave_Gap_Days': 150,
            'Remote_Posting': 'Yes',
            'Operational_Exposure': 'High'
        }

        result = predict_welfare(sample_critical_record)
        
        # Verify required keys exist
        for key in ['stress_level', 'risk_score', 'risk_priority', 'probabilities', 'key_factors', 'recommendations', 'disclaimer']:
            self.assertIn(key, result)
            
        # Verify types and logical ranges
        self.assertIn(result['stress_level'], ['Low', 'Medium', 'High'])
        self.assertTrue(0 <= result['risk_score'] <= 100)
        self.assertIn(result['risk_priority'], ['Routine', 'Preventive', 'Priority'])
        self.assertIsInstance(result['probabilities'], dict)
        self.assertIsInstance(result['key_factors'], list)
        self.assertIsInstance(result['recommendations'], list)
        self.assertGreater(len(result['key_factors']), 0)
        self.assertGreater(len(result['recommendations']), 0)

if __name__ == '__main__':
    unittest.main()

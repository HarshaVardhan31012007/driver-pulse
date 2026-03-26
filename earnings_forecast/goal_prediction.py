import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from enum import Enum


class GoalStatus(Enum):
    GOAL_ALREADY_ACHIEVED = "GOAL_ALREADY_ACHIEVED"
    GOAL_ON_TRACK = "GOAL_ON_TRACK"
    GOAL_AT_RISK = "GOAL_AT_RISK"
    GOAL_LIKELY_MISSED = "GOAL_LIKELY_MISSED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class GoalPredictor:

    def __init__(self):
        self.MIN_HOURS_FOR_PREDICTION = 1
        self.ON_TRACK_THRESHOLD = 0.75
        self.AT_RISK_THRESHOLD = 0.40

    def predict_goal_achievement(
        self,
        goals_df: pd.DataFrame,
        velocity_metrics: pd.DataFrame,
        forecasts: pd.DataFrame
    ) -> pd.DataFrame:

        merged_data = goals_df.merge(velocity_metrics, on="driver_id", how="left")

        results = []

        for _, row in merged_data.iterrows():
            prediction = self._predict_single_driver_goal(row.to_dict())
            results.append(prediction)

        return pd.DataFrame(results)

    def _predict_single_driver_goal(self, driver_data: Dict) -> Dict:

        def _safe(value, default=0):
            return default if pd.isna(value) else value

        driver_id = driver_data['driver_id']
        daily_goal = driver_data['daily_goal']

        current_earnings = _safe(driver_data.get('current_earnings', 0))
        current_hours = _safe(driver_data.get('current_hours_worked', 0))
        current_velocity = _safe(driver_data.get('current_velocity', 0))
        avg_velocity = _safe(driver_data.get('avg_earnings_per_hour', 0))

        progress_percentage = (
            min(100.0, (current_earnings / daily_goal) * 100)
            if daily_goal > 0 else 0
        )

        if progress_percentage >= 100:
            status = GoalStatus.GOAL_ALREADY_ACHIEVED
            probability = 1.0
            estimated_completion_time = datetime.now()

        elif current_hours < self.MIN_HOURS_FOR_PREDICTION:
            status = GoalStatus.INSUFFICIENT_DATA
            probability = self._estimate_cold_start_probability(
                progress_percentage, current_hours
            )
            estimated_completion_time = None

        else:
            status, probability, estimated_completion_time = self._calculate_goal_status(
                driver_data, progress_percentage
            )

        recommendations = self._generate_recommendations(
            status, progress_percentage, driver_data
        )

        return {
            'driver_id': driver_id,
            'daily_goal': daily_goal,
            'current_earnings': current_earnings,
            'current_hours_worked': current_hours,
            'progress_percentage': progress_percentage,
            'goal_status': status.value,
            'achievement_probability': probability,
            'estimated_completion_time': (
                estimated_completion_time.isoformat()
                if estimated_completion_time else None
            ),
            'earnings_needed': max(0, daily_goal - current_earnings),
            'recommended_hours_remaining': self._calculate_needed_hours(
                daily_goal, current_earnings, driver_data
            ),
            'recommendations': " | ".join(recommendations),
            'last_updated': datetime.now().isoformat()
        }

    def _calculate_goal_status(self, driver_data: Dict, progress: float):

        current_velocity = driver_data.get('current_velocity', 0)
        avg_velocity = driver_data.get('avg_earnings_per_hour', 0)
        current_hours = driver_data.get('current_hours_worked', 0)
        daily_goal = driver_data.get('daily_goal', 0)
        current_earnings = driver_data.get('current_earnings', 0)

        effective_velocity = current_velocity if current_velocity > 0 else avg_velocity

        if effective_velocity <= 0:
            return GoalStatus.INSUFFICIENT_DATA, 0.3, None

        remaining_earnings = daily_goal - current_earnings
        hours_needed = remaining_earnings / effective_velocity if effective_velocity > 0 else 0

        probability = min(1.0, progress / 100 + 0.3)

        if probability >= self.ON_TRACK_THRESHOLD:
            status = GoalStatus.GOAL_ON_TRACK
        elif probability >= self.AT_RISK_THRESHOLD:
            status = GoalStatus.GOAL_AT_RISK
        else:
            status = GoalStatus.GOAL_LIKELY_MISSED

        estimated_time = datetime.now() + timedelta(hours=hours_needed)

        return status, probability, estimated_time

    def _calculate_needed_hours(self, daily_goal, current_earnings, driver_data):

        avg_velocity = driver_data.get('avg_earnings_per_hour', 0)

        if avg_velocity <= 0:
            return None

        remaining = max(0, daily_goal - current_earnings)
        return round(remaining / avg_velocity, 2)

    def _estimate_cold_start_probability(self, progress, hours):
        return min(1.0, (progress / 100) * 0.5 + (hours * 0.1))

    def _generate_recommendations(self, status, progress, driver_data):

        rec = []

        if status == GoalStatus.GOAL_ALREADY_ACHIEVED:
            rec += ["🎉 Goal achieved!", "Take a break or earn bonus"]

        elif status == GoalStatus.GOAL_ON_TRACK:
            rec += ["✅ On track", "Maintain pace"]

        elif status == GoalStatus.GOAL_AT_RISK:
            rec += ["⚠️ At risk", "Drive in peak hours"]
            if progress < 50:
                rec.append("Focus on long trips")

        elif status == GoalStatus.GOAL_LIKELY_MISSED:
            rec += ["❌ Likely miss", "Increase hours", "Adjust goal"]

        else:
            rec.append("📊 Need more data")

        return rec

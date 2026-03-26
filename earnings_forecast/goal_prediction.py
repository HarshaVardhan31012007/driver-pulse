import pandas as pd
from datetime import datetime, timedelta
from typing import Dict
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

    def predict_goal_achievement(self, goals_df, velocity_metrics, forecasts):
        merged_data = goals_df.merge(velocity_metrics, on="driver_id", how="left")

        results = []
        for _, row in merged_data.iterrows():
            results.append(self._predict_single_driver_goal(row.to_dict()))

        return pd.DataFrame(results)

    def _predict_single_driver_goal(self, driver_data: Dict):

        def _safe(value, default=0):
            return default if pd.isna(value) else value

        driver_id = driver_data['driver_id']
        daily_goal = driver_data['daily_goal']

        current_earnings = _safe(driver_data.get('current_earnings', 0))
        current_hours = _safe(driver_data.get('current_hours_worked', 0))
        current_velocity = _safe(driver_data.get('current_velocity', 0))
        avg_velocity = _safe(driver_data.get('avg_earnings_per_hour', 0))

        progress = (current_earnings / daily_goal) * 100 if daily_goal > 0 else 0

        if progress >= 100:
            status = GoalStatus.GOAL_ALREADY_ACHIEVED
            probability = 1.0
            est_time = datetime.now()

        elif current_hours < self.MIN_HOURS_FOR_PREDICTION:
            status = GoalStatus.INSUFFICIENT_DATA
            probability = 0.3
            est_time = None

        else:
            status, probability, est_time = self._calculate_goal_status(driver_data, progress)

        rec = self._generate_recommendations(status, progress)

        return {
            "driver_id": driver_id,
            "goal_status": status.value,
            "recommendations": " | ".join(rec)
        }

    def _calculate_goal_status(self, data, progress):
        velocity = data.get('current_velocity', 0) or data.get('avg_earnings_per_hour', 0)

        if velocity <= 0:
            return GoalStatus.INSUFFICIENT_DATA, 0.3, None

        prob = min(1.0, progress / 100 + 0.3)

        if prob >= self.ON_TRACK_THRESHOLD:
            status = GoalStatus.GOAL_ON_TRACK
        elif prob >= self.AT_RISK_THRESHOLD:
            status = GoalStatus.GOAL_AT_RISK
        else:
            status = GoalStatus.GOAL_LIKELY_MISSED

        return status, prob, datetime.now()

    def _generate_recommendations(self, status, progress):
        rec = []

        if status == GoalStatus.GOAL_ALREADY_ACHIEVED:
            rec += ["🎉 Goal achieved!", "Take a break"]

        elif status == GoalStatus.GOAL_ON_TRACK:
            rec += ["✅ On track", "Maintain pace"]

        elif status == GoalStatus.GOAL_AT_RISK:
            rec += ["⚠️ At risk", "Drive in peak hours"]
            if progress < 50:
                rec.append("Focus on long trips")

        elif status == GoalStatus.GOAL_LIKELY_MISSED:
            rec += ["❌ Likely miss", "Increase hours"]

        else:
            rec.append("📊 Need more data")

        return rec

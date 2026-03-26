import pandas as pd
from datetime import datetime
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

    def predict_goal_achievement(self, goals_df, velocity_metrics, forecasts):
        merged = goals_df.merge(velocity_metrics, on="driver_id", how="left")

        results = []
        for _, row in merged.iterrows():
            results.append(self._predict(row.to_dict()))

        return pd.DataFrame(results)

    def _predict(self, data):

        driver_id = data['driver_id']
        goal = data['daily_goal']
        earnings = data.get('current_earnings', 0)
        hours = data.get('current_hours_worked', 0)
        velocity = data.get('current_velocity', 0) or data.get('avg_earnings_per_hour', 0)

        progress = (earnings / goal) * 100 if goal > 0 else 0

        # 🎯 STATUS LOGIC
        if progress >= 100:
            status = GoalStatus.GOAL_ALREADY_ACHIEVED

        elif hours < self.MIN_HOURS_FOR_PREDICTION:
            status = GoalStatus.INSUFFICIENT_DATA

        elif progress >= 70:
            status = GoalStatus.GOAL_ON_TRACK

        elif progress >= 40:
            status = GoalStatus.GOAL_AT_RISK

        else:
            status = GoalStatus.GOAL_LIKELY_MISSED

        # 🔥 SMART GOAL SUGGESTION
        suggested_goal = self._suggest_goal(data)

        return {
            "driver_id": driver_id,
            "daily_goal": goal,
            "current_earnings": earnings,
            "progress_percentage": round(progress, 1),  # ✅ FIXED NAME
            "goal_status": status.value,
            "recommended_goal": suggested_goal,
            "recommendations": self._recommend(status)
        }

    def _suggest_goal(self, data):
        earnings = data.get('current_earnings', 0)
        hours = data.get('current_hours_worked', 0)
        velocity = data.get('avg_earnings_per_hour', 0)

        if velocity <= 0:
            return None

        remaining_hours = max(0, 8 - hours)
        possible = earnings + (remaining_hours * velocity)

        return round(possible * 0.9, 0)

    def _recommend(self, status):

        if status == GoalStatus.GOAL_ALREADY_ACHIEVED:
            return "🎉 Goal achieved! Earn bonus"

        elif status == GoalStatus.GOAL_ON_TRACK:
            return "✅ Maintain pace"

        elif status == GoalStatus.GOAL_AT_RISK:
            return "⚠️ Drive in peak hours"

        elif status == GoalStatus.GOAL_LIKELY_MISSED:
            return "❌ Increase hours"

        return "📊 Need more data"

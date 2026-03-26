"""
Goal Prediction Module
Predicts driver goal achievement and provides status classification.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum


class GoalStatus(Enum):
    GOAL_ON_TRACK = "GOAL_ON_TRACK"
    GOAL_AT_RISK = "GOAL_AT_RISK"
    GOAL_LIKELY_MISSED = "GOAL_LIKELY_MISSED"
    GOAL_ALREADY_ACHIEVED = "GOAL_ALREADY_ACHIEVED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class GoalPredictor:
    
    def __init__(self):
        self.ON_TRACK_THRESHOLD = 0.8
        self.AT_RISK_THRESHOLD = 0.5
        self.MIN_HOURS_FOR_PREDICTION = 1.0
        
        self.PEAK_HOURS_MULTIPLIER = 1.3
        self.OFF_PEAK_HOURS_MULTIPLIER = 0.8
        
        self.COLD_START_PROGRESS_RATE = 0.15
        self.TYPICAL_DAILY_HOURS = 8.0

    # ================= MAIN FUNCTION =================
    def predict_goal_achievement(self, goals_df, velocity_metrics, forecasts):
        results = []

        merged_data = self._merge_goal_data(goals_df, velocity_metrics, forecasts)

        for _, row in merged_data.iterrows():
            prediction = self._predict_single_driver_goal(row.to_dict())
            results.append(prediction)   # ✅ FIXED

        return pd.DataFrame(results)

    # ================= MERGE =================
    def _merge_goal_data(self, goals_df, velocity_metrics, forecasts):
        merged = goals_df.copy()

        if not velocity_metrics.empty:
            merged = merged.merge(velocity_metrics, on='driver_id', how='left')

        if not forecasts.empty:
            merged = merged.merge(
                forecasts,
                on='driver_id',
                how='left',
                suffixes=('', '_forecast')
            )

        return merged

    # ================= SINGLE DRIVER =================
    def _predict_single_driver_goal(self, driver_data):

        def _safe(value, default=0):
            return default if pd.isna(value) else value

        driver_id = driver_data['driver_id']
        daily_goal = driver_data['daily_goal']

        current_earnings = _safe(driver_data.get('current_earnings', 0))
        current_hours = _safe(driver_data.get('current_hours_worked', 0))

        progress_percentage = (
            min(100.0, (current_earnings / daily_goal) * 100)
            if daily_goal > 0 else 0
        )

        if progress_percentage >= 100:
            status = GoalStatus.GOAL_ALREADY_ACHIEVED
            achievement_probability = 1.0
            estimated_completion_time = datetime.now()

        elif current_hours < self.MIN_HOURS_FOR_PREDICTION:
            status = GoalStatus.INSUFFICIENT_DATA
            achievement_probability = self._estimate_cold_start_probability(
                progress_percentage, current_hours
            )
            estimated_completion_time = None

        else:
            status, achievement_probability, estimated_completion_time = \
                self._calculate_goal_status(driver_data, progress_percentage)

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
            'achievement_probability': achievement_probability,
            'estimated_completion_time': (
                estimated_completion_time.isoformat()
                if estimated_completion_time else None
            ),
            'earnings_needed': max(0, daily_goal - current_earnings),
            'recommended_hours_remaining': self._calculate_needed_hours(
                daily_goal, current_earnings, driver_data
            ),
            'recommendations': " | ".join(recommendations),   # ✅ UI FRIENDLY
            'last_updated': datetime.now().isoformat()
        }

    # ================= STATUS =================
    def _calculate_goal_status(self, driver_data, progress_percentage):

        current_earnings = driver_data.get('current_earnings', 0)
        daily_goal = driver_data['daily_goal']

        avg_velocity = driver_data.get('avg_earnings_per_hour', 15.0)

        hour = datetime.now().hour
        adjusted_velocity = avg_velocity * self._get_time_multiplier(hour)

        earnings_needed = daily_goal - current_earnings

        hours_needed = earnings_needed / adjusted_velocity if adjusted_velocity > 0 else float('inf')

        remaining_hours = self._get_remaining_work_hours()

        if hours_needed <= remaining_hours:
            probability = min(1.0, remaining_hours / (hours_needed + 0.1))
        else:
            probability = max(0.0, remaining_hours / hours_needed)

        if probability >= self.ON_TRACK_THRESHOLD:
            status = GoalStatus.GOAL_ON_TRACK
        elif probability >= self.AT_RISK_THRESHOLD:
            status = GoalStatus.GOAL_AT_RISK
        else:
            status = GoalStatus.GOAL_LIKELY_MISSED

        estimated_time = datetime.now() + timedelta(hours=hours_needed) if probability > 0.5 else None

        return status, probability, estimated_time

    # ================= COLD START =================
    def _estimate_cold_start_probability(self, progress, hours):
        expected = (hours / self.TYPICAL_DAILY_HOURS) * 100
        ratio = progress / expected if expected > 0 else 0

        if ratio >= 1.2: return 0.9
        elif ratio >= 1.0: return 0.8
        elif ratio >= 0.8: return 0.6
        elif ratio >= 0.6: return 0.4
        else: return 0.2

    # ================= TIME =================
    def _get_time_multiplier(self, hour):
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return self.PEAK_HOURS_MULTIPLIER
        elif 20 <= hour <= 23:
            return 1.1
        elif 10 <= hour <= 16:
            return 1.0
        else:
            return self.OFF_PEAK_HOURS_MULTIPLIER

    def _get_remaining_work_hours(self):
        now = datetime.now()
        end = now.replace(hour=22, minute=0, second=0, microsecond=0)
        return max(0, (end - now).total_seconds() / 3600)

    # ================= HOURS =================
    def _calculate_needed_hours(self, goal, earnings, driver_data):
        needed = max(0, goal - earnings)
        avg_velocity = driver_data.get('avg_earnings_per_hour', 15.0)
        adjusted = avg_velocity * self._get_time_multiplier(datetime.now().hour)

        return needed / adjusted if adjusted > 0 else float('inf')

    # ================= RECOMMENDATIONS =================
    def _generate_recommendations(self, status, progress, driver_data):

        if isinstance(status, str):
            status = GoalStatus(status)

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

    # ================= METRICS =================
    def calculate_goal_metrics(self, predictions):
        if predictions.empty:
            return {}

        return {
            'total_drivers': len(predictions),
            'average_progress': predictions['progress_percentage'].mean(),
            'average_probability': predictions['achievement_probability'].mean()
        }

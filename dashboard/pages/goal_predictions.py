import streamlit as st
import pandas as pd

# ✅ FIXED IMPORT
from earnings_forecast.goal_prediction import GoalPredictor


def main():
    st.title("🎯 Goal Predictions")

    predictor = GoalPredictor()

    # ✅ TEMP DATA (so it works 100%)
    goals_df = pd.DataFrame({
        "driver_id": [101, 102, 103],
        "daily_goal": [2000, 2500, 1800]
    })

    velocity_metrics = pd.DataFrame({
        "driver_id": [101, 102, 103],
        "current_earnings": [900, 2200, 500],
        "current_hours_worked": [3, 6, 2],
        "current_velocity": [300, 400, 200],
        "avg_earnings_per_hour": [280, 350, 220]
    })

    forecasts = pd.DataFrame()

    predictions = predictor.predict_goal_achievement(
        goals_df, velocity_metrics, forecasts
    )

    st.dataframe(predictions, use_container_width=True)


if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
from goal_predictor import GoalPredictor


def main():
    st.set_page_config(page_title="Goal Predictions", layout="wide")

    st.title("🎯 Driver Goal Predictions")

    predictor = GoalPredictor()

    # 🔥 DUMMY DATA (IMPORTANT — so it ALWAYS works)
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

    forecasts = pd.DataFrame()  # not used for now

    predictions = predictor.predict_goal_achievement(
        goals_df, velocity_metrics, forecasts
    )

    st.dataframe(predictions, use_container_width=True)


if __name__ == "__main__":
    main()

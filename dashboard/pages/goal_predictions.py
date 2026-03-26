import streamlit as st
from app import DriverPulseDashboard
from goal_predictor import GoalPredictor   # your file

def main():
    st.title("🎯 Goal Predictions")

    dashboard = DriverPulseDashboard()

    predictor = GoalPredictor()

    # You MUST have these
    goals_df = dashboard.data['goals']
    velocity_metrics = dashboard.data['velocity_metrics']
    forecasts = dashboard.data['forecasts']

    predictions = predictor.predict_goal_achievement(
        goals_df, velocity_metrics, forecasts
    )

    st.dataframe(predictions[['driver_id', 'goal_status', 'recommendations']])

if __name__ == "__main__":
    main()

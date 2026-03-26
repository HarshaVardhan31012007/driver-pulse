import streamlit as st
import pandas as pd
from earnings_forecast.goal_prediction import GoalPredictor


def main():
    st.set_page_config(layout="wide")

    st.title("🎯 Goal Predictions")

    predictor = GoalPredictor()

    # 🔥 DEMO DATA (replace later with dashboard.data)
    goals_df = pd.DataFrame({
        "driver_id": [101, 102, 103],
        "daily_goal": [2000, 2500, 1800]
    })

    velocity_metrics = pd.DataFrame({
        "driver_id": [101, 102, 103],
        "current_earnings": [900, 2200, 500],
        "current_hours_worked": [3, 6, 2],
        "avg_earnings_per_hour": [280, 350, 220]
    })

    forecasts = pd.DataFrame()

    predictions = predictor.predict_goal_achievement(
        goals_df, velocity_metrics, forecasts
    )

    # 🎨 UI CARDS
    st.subheader("📊 Driver Goal Insights")

    for _, row in predictions.iterrows():

        status = row.get('goal_status', 'UNKNOWN')
        progress = row.get('progress_percentage', 0)
    
        color = {
            "GOAL_ON_TRACK": "green",
            "GOAL_AT_RISK": "orange",
            "GOAL_LIKELY_MISSED": "red",
            "GOAL_ALREADY_ACHIEVED": "blue",
            "INSUFFICIENT_DATA": "gray"
        }.get(status, "gray")
    
        st.markdown(f"""
        <div style="
            padding:15px;
            border-radius:10px;
            margin-bottom:10px;
            background-color:#111;
            border-left:5px solid {color};
        ">
            <h4>🚗 Driver {row.get('driver_id')}</h4>
            <p><b>Status:</b> {status}</p>
            <p><b>Progress:</b> {progress}%</p>
            <p><b>Goal:</b> ₹{row.get('daily_goal')}</p>
            <p><b>Suggested Goal:</b> ₹{row.get('recommended_goal')}</p>
            <p><b>Advice:</b> {row.get('recommendations')}</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 📋 TABLE
    st.subheader("📋 Raw Data")
    st.dataframe(predictions, use_container_width=True)


if __name__ == "__main__":
    main()

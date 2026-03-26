"""
Earnings Trends Page - Detailed earnings analysis and financial trends
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import config

# Import dashboard class
from app import DriverPulseDashboard

def main():
    """Earnings trends page with detailed financial analysis."""
    
    # Page header
    st.markdown('''
    <div style="
        background: linear-gradient(135deg, #fd7e14 0%, #e8590c 100%);
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 15px 40px rgba(253, 126, 20, 0.3);
    ">
        <h1 style="
            color: white; 
            margin: 0; 
            font-size: 2.5rem;
            font-weight: 800;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        ">
            💎 Earnings Trends
        </h1>
        <p style="
            color: rgba(255,255,255,0.95);
            margin: 1rem 0 0 0;
            font-size: 1.2rem;
            font-weight: 400;
        ">
            Comprehensive earnings analysis, financial trends, and revenue optimization insights
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Initialize dashboard
    dashboard = DriverPulseDashboard()
    
    if 'trips' not in dashboard.data:
        st.error('No trip data available for earnings analysis.')
        return
    
    trips = dashboard.data['trips'].copy()
    
    # Sidebar filters
    st.sidebar.markdown('### 🎛️ Earnings Filters')
    
    # Time period filter
    time_period = st.sidebar.selectbox(
        'Time Period:',
        ['Last 7 Days', 'Last 30 Days', 'Last 90 Days', 'All Time'],
        help='Select time period for earnings analysis'
    )
    
    # Driver filter
    if 'driver_metrics' in dashboard.data:
        drivers = ['All Drivers'] + sorted(dashboard.data['driver_metrics']['driver_id'].unique().tolist())
        selected_driver = st.sidebar.selectbox('Driver:', drivers)
    else:
        selected_driver = 'All Drivers'
    
    # Earnings metric filter
    earnings_metric = st.sidebar.selectbox(
        'Primary Metric:',
        ['Total Earnings', 'Earnings per Hour', 'Earnings per Trip', 'Earnings per Mile'],
        help='Choose primary earnings metric for analysis'
    )
    
    # Apply filters
    trips['start_time'] = pd.to_datetime(trips['start_time'])
    
    # Filter by time period
    if time_period != 'All Time':
        now = datetime.now()
        if time_period == 'Last 7 Days':
            start_date = now - timedelta(days=7)
        elif time_period == 'Last 30 Days':
            start_date = now - timedelta(days=30)
        elif time_period == 'Last 90 Days':
            start_date = now - timedelta(days=90)
        
        trips = trips[trips['start_time'] >= start_date]
    
    # Filter by driver
    if selected_driver != 'All Drivers':
        trips = trips[trips['driver_id'] == selected_driver]
    
    if trips.empty:
        st.warning('No trip data matches the selected filters.')
        return
    
    # Earnings overview
    st.markdown('### 💰 Earnings Overview')
    
    # Calculate key metrics
    total_earnings = trips['fare'].sum()
    total_earnings_inr = total_earnings * 83
    avg_earnings_per_hour = trips['earnings_per_minute'].mean() * 60
    avg_earnings_per_trip = trips['fare'].mean()
    total_trips = len(trips)
    total_hours = trips['duration_minutes'].sum() / 60
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Earnings",
            value=f"₹{total_earnings_inr:,.0f}",
            delta=f"{total_trips} trips"
        )
    
    with col2:
        st.metric(
            label="⚡ Avg Earnings/Hour",
            value=f"₹{avg_earnings_per_hour * 83:.0f}",
            delta="per hour"
        )
    
    with col3:
        st.metric(
            label="🚗 Avg Earnings/Trip",
            value=f"₹{avg_earnings_per_trip * 83:.0f}",
            delta="per trip"
        )
    
    with col4:
        st.metric(
            label="⏱️ Total Hours",
            value=f"{total_hours:.1f}",
            delta="driven"
        )
    
    # Earnings trends over time
    st.markdown('### 📈 Earnings Trends Analysis')
    
    # Prepare time series data
    trips['date'] = trips['start_time'].dt.date
    trips['hour'] = trips['start_time'].dt.hour
    trips['day_of_week'] = trips['start_time'].dt.day_name()
    
    # Daily earnings
    daily_earnings = trips.groupby('date').agg({
        'fare': 'sum',
        'earnings_per_minute': 'mean',
        'trip_id': 'count',
        'duration_minutes': 'sum'
    }).reset_index()
    
    daily_earnings['earnings_per_hour'] = daily_earnings['earnings_per_minute'] * 60
    daily_earnings['avg_trip_fare'] = daily_earnings['fare'] / daily_earnings['trip_id']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily earnings trend
        fig_trend = px.line(
            daily_earnings,
            x='date',
            y='fare',
            title='Daily Earnings Trend',
            labels={'fare': 'Total Earnings ($)', 'date': 'Date'},
            color_discrete_sequence=['#fd7e14']
        )
        
        fig_trend.update_traces(line_width=3)
        fig_trend.update_layout(height=400)
        st.plotly_chart(fig_trend, width='stretch')
    
    with col2:
        # Earnings per hour trend
        fig_hourly = px.line(
            daily_earnings,
            x='date',
            y='earnings_per_hour',
            title='Earnings per Hour Trend',
            labels={'earnings_per_hour': 'Earnings ($/hour)', 'date': 'Date'},
            color_discrete_sequence=['#28a745']
        )
        
        fig_hourly.update_traces(line_width=3)
        fig_hourly.update_layout(height=400)
        st.plotly_chart(fig_hourly, width='stretch')
    
    # Time-based earnings patterns
    st.markdown('### ⏰ Time-Based Earnings Patterns')
    
    # Hourly earnings analysis
    hourly_earnings = trips.groupby('hour').agg({
        'fare': 'mean',
        'earnings_per_minute': 'mean',
        'trip_id': 'count'
    }).reset_index()
    
    hourly_earnings['earnings_per_hour'] = hourly_earnings['earnings_per_minute'] * 60
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Hourly earnings pattern
        fig_hour_pattern = px.bar(
            hourly_earnings,
            x='hour',
            y='earnings_per_hour',
            title='Average Earnings by Hour of Day',
            labels={'hour': 'Hour', 'earnings_per_hour': 'Earnings ($/hour)'},
            color_discrete_sequence=['#17a2b8']
        )
        
        fig_hour_pattern.update_layout(height=400)
        st.plotly_chart(fig_hour_pattern, width='stretch')
    
    with col2:
        # Trip frequency by hour
        fig_trip_freq = px.bar(
            hourly_earnings,
            x='hour',
            y='trip_id',
            title='Trip Frequency by Hour',
            labels={'hour': 'Hour', 'trip_id': 'Number of Trips'},
            color_discrete_sequence=['#6f42c1']
        )
        
        fig_trip_freq.update_layout(height=400)
        st.plotly_chart(fig_trip_freq, width='stretch')
    
    # Day of week analysis
    st.markdown('### 📅 Day of Week Earnings Analysis')
    
    # Day of week earnings
    daily_earnings_by_dow = trips.groupby('day_of_week').agg({
        'fare': 'sum',
        'earnings_per_minute': 'mean',
        'trip_id': 'count',
        'duration_minutes': 'sum'
    }).reset_index()
    
    daily_earnings_by_dow['earnings_per_hour'] = daily_earnings_by_dow['earnings_per_minute'] * 60
    
    # Order days properly
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_earnings_by_dow['day_of_week'] = pd.Categorical(
        daily_earnings_by_dow['day_of_week'], 
        categories=day_order, 
        ordered=True
    )
    daily_earnings_by_dow = daily_earnings_by_dow.sort_values('day_of_week')
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Earnings by day of week
        fig_dow_earnings = px.bar(
            daily_earnings_by_dow,
            x='day_of_week',
            y='fare',
            title='Total Earnings by Day of Week',
            labels={'day_of_week': 'Day', 'fare': 'Total Earnings ($)'},
            color_discrete_sequence=['#ffc107']
        )
        
        fig_dow_earnings.update_layout(height=400)
        st.plotly_chart(fig_dow_earnings, width='stretch')
    
    with col2:
        # Earnings per hour by day
        fig_dow_hourly = px.bar(
            daily_earnings_by_dow,
            x='day_of_week',
            y='earnings_per_hour',
            title='Earnings per Hour by Day',
            labels={'day_of_week': 'Day', 'earnings_per_hour': 'Earnings ($/hour)'},
            color_discrete_sequence=['#20c997']
        )
        
        fig_dow_hourly.update_layout(height=400)
        st.plotly_chart(fig_dow_hourly, width='stretch')
    
    # Top performers analysis
    st.markdown('### 🏆 Top Earners Analysis')
    
    if selected_driver == 'All Drivers':
        # Driver earnings ranking
        driver_earnings = trips.groupby('driver_id').agg({
            'fare': 'sum',
            'earnings_per_minute': 'mean',
            'trip_id': 'count',
            'duration_minutes': 'sum'
        }).reset_index()
        
        driver_earnings['earnings_per_hour'] = driver_earnings['earnings_per_minute'] * 60
        driver_earnings['avg_trip_fare'] = driver_earnings['fare'] / driver_earnings['trip_id']
        
        # Sort by total earnings
        top_earners = driver_earnings.sort_values('fare', ascending=False).head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top earners by total earnings
            fig_top_earners = px.bar(
                top_earners,
                x='driver_id',
                y='fare',
                title='Top 10 Drivers by Total Earnings',
                labels={'driver_id': 'Driver ID', 'fare': 'Total Earnings ($)'},
                color_discrete_sequence=['#28a745']
            )
            
            fig_top_earners.update_layout(height=400)
            st.plotly_chart(fig_top_earners, width='stretch')
        
        with col2:
            # Top earners by earnings per hour
            top_hourly = driver_earnings.sort_values('earnings_per_hour', ascending=False).head(10)
            
            fig_top_hourly = px.bar(
                top_hourly,
                x='driver_id',
                y='earnings_per_hour',
                title='Top 10 Drivers by Earnings/Hour',
                labels={'driver_id': 'Driver ID', 'earnings_per_hour': 'Earnings ($/hour)'},
                color_discrete_sequence=['#17a2b8']
            )
            
            fig_top_hourly.update_layout(height=400)
            st.plotly_chart(fig_top_hourly, width='stretch')
    
    # Earnings distribution analysis
    st.markdown('### 📊 Earnings Distribution Analysis')
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Trip fare distribution
        fig_fare_dist = px.histogram(
            trips,
            x='fare',
            title='Trip Fare Distribution',
            labels={'fare': 'Fare ($)', 'count': 'Number of Trips'},
            nbins=20,
            color_discrete_sequence=['#fd7e14']
        )
        
        fig_fare_dist.update_layout(height=400)
        st.plotly_chart(fig_fare_dist, width='stretch')
    
    with col2:
        # Earnings per minute distribution
        fig_epm_dist = px.histogram(
            trips,
            x='earnings_per_minute',
            title='Earnings per Minute Distribution',
            labels={'earnings_per_minute': 'Earnings ($/min)', 'count': 'Number of Trips'},
            nbins=20,
            color_discrete_sequence=['#6f42c1']
        )
        
        fig_epm_dist.update_layout(height=400)
        st.plotly_chart(fig_epm_dist, width='stretch')
    
    # Performance optimization insights
    st.markdown('### 💡 Earnings Optimization Insights')
    
    # Generate insights
    insights = []
    
    # Best earning hours
    best_hour = hourly_earnings.loc[hourly_earnings['earnings_per_hour'].idxmax()]
    insights.append({
        'type': 'Peak Earning Time',
        'message': f"Highest earnings occur between {best_hour['hour']}:00-{best_hour['hour']+1}:00 with an average of ₹{best_hour['earnings_per_hour'] * 83:.0f}/hour.",
        'priority': 'High',
        'action': 'Focus driving during these peak hours for maximum earnings'
    })
    
    # Best earning day
    best_day = daily_earnings_by_dow.loc[daily_earnings_by_dow['earnings_per_hour'].idxmax()]
    insights.append({
        'type': 'Best Earning Day',
        'message': f"{best_day['day_of_week']} has the highest earnings per hour at ₹{best_day['earnings_per_hour'] * 83:.0f}/hour.",
        'priority': 'Medium',
        'action': 'Prioritize availability on this day'
    })
    
    # High-value trips analysis
    high_value_threshold = trips['fare'].quantile(0.8)
    high_value_trips = trips[trips['fare'] >= high_value_threshold]
    
    if len(high_value_trips) > 0:
        avg_high_value_duration = high_value_trips['duration_minutes'].mean()
        insights.append({
            'type': 'High-Value Trips',
            'message': f"Top 20% of trips by value have an average duration of {avg_high_value_duration:.1f} minutes and generate ₹{high_value_trips['fare'].mean() * 83:.0f} per trip.",
            'priority': 'Medium',
            'action': 'Identify and target similar high-value trip patterns'
        })
    
    # Earnings consistency
    earnings_std = daily_earnings['fare'].std()
    earnings_mean = daily_earnings['fare'].mean()
    consistency_score = (earnings_mean - earnings_std) / earnings_mean * 100
    
    if consistency_score < 70:
        insights.append({
            'type': 'Earnings Consistency',
            'message': f"Earnings show high variability (consistency score: {consistency_score:.1f}%). Consider steadier driving patterns.",
            'priority': 'Medium',
            'action': 'Work on more consistent driving schedule and trip acceptance'
        })
    
    # Display insights
    for insight in insights:
        priority_color = {
            'High': '#dc3545',
            'Medium': '#ffc107',
            'Low': '#28a745'
        }[insight['priority']]
        
        st.markdown(f'''
        <div style="
            background: linear-gradient(135deg, {priority_color}22 0%, {priority_color}11 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            border-left: 4px solid {priority_color};
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <h4 style="color: {priority_color}; margin: 0 0 0.5rem 0;">
                        {insight['type']}
                    </h4>
                    <p style="margin: 0 0 0.5rem 0; color: #495057; line-height: 1.5;">
                        {insight['message']}
                    </p>
                    <p style="margin: 0; color: #6c757d; font-style: italic; font-size: 0.9rem;">
                        💡 {insight['action']}
                    </p>
                </div>
                <span style="
                    background: {priority_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: bold;
                    margin-left: 1rem;
                ">
                    {insight['priority']}
                </span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Detailed earnings table
    st.markdown('### 📋 Detailed Earnings Data')
    
    # Prepare earnings summary table
    if selected_driver == 'All Drivers':
        earnings_summary = driver_earnings[[
            'driver_id', 'fare', 'earnings_per_hour', 'trip_id', 'avg_trip_fare'
        ]].copy()
        earnings_summary.columns = [
            'Driver ID', 'Total Earnings ($)', 'Earnings/Hour ($)', 
            'Number of Trips', 'Avg Trip Fare ($)'
        ]
        earnings_summary['Total Earnings ($)'] = earnings_summary['Total Earnings ($)'].apply(
            lambda x: f"₹{x * 83:.2f}"
        )
        earnings_summary['Earnings/Hour ($)'] = earnings_summary['Earnings/Hour ($)'].apply(
            lambda x: f"₹{x * 83:.2f}"
        )
        earnings_summary['Avg Trip Fare ($)'] = earnings_summary['Avg Trip Fare ($)'].apply(
            lambda x: f"₹{x * 83:.2f}"
        )
    else:
        # Single driver daily breakdown
        earnings_summary = daily_earnings[[
            'date', 'fare', 'earnings_per_hour', 'trip_id', 'avg_trip_fare'
        ]].copy()
        earnings_summary.columns = [
            'Date', 'Total Earnings ($)', 'Earnings/Hour ($)', 
            'Number of Trips', 'Avg Trip Fare ($)'
        ]
        earnings_summary['Date'] = earnings_summary['Date'].astype(str)
        earnings_summary['Total Earnings ($)'] = earnings_summary['Total Earnings ($)'].apply(
            lambda x: f"₹{x * 83:.2f}"
        )
        earnings_summary['Earnings/Hour ($)'] = earnings_summary['Earnings/Hour ($)'].apply(
            lambda x: f"₹{x * 83:.2f}"
        )
        earnings_summary['Avg Trip Fare ($)'] = earnings_summary['Avg Trip Fare ($)'].apply(
            lambda x: f"₹{x * 83:.2f}"
        )
    
    st.dataframe(earnings_summary, width='stretch')
    
    # Export functionality
    st.markdown('### 📤 Export Earnings Data')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button('📊 Download Earnings Report', type='primary'):
            # Create earnings report
            report_data = {
                'Report Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Time Period': time_period,
                'Driver Filter': selected_driver,
                'Total Earnings ($)': f"{total_earnings:.2f}",
                'Total Earnings (₹)': f"{total_earnings_inr:.2f}",
                'Average Earnings/Hour ($)': f"{avg_earnings_per_hour:.2f}",
                'Average Earnings/Hour (₹)': f"{avg_earnings_per_hour * 83:.2f}",
                'Total Trips': total_trips,
                'Total Hours': f"{total_hours:.2f}",
                'Average Trip Fare ($)': f"{avg_earnings_per_trip:.2f}",
                'Average Trip Fare (₹)': f"{avg_earnings_per_trip * 83:.2f}"
            }
            
            # Add insights
            for i, insight in enumerate(insights, 1):
                report_data[f'Insight {i}'] = f"{insight['type']}: {insight['message']}"
            
            report_df = pd.DataFrame(list(report_data.items()), columns=['Metric', 'Value'])
            csv_data = report_df.to_csv(index=False)
            
            st.download_button(
                label='Download Earnings Report',
                data=csv_data,
                file_name=f'earnings_trends_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv'
            )
    
    with col2:
        if st.button('📈 Download Raw Earnings Data', type='secondary'):
            # Export filtered earnings data
            export_data = earnings_summary.copy()
            csv_data = export_data.to_csv(index=False)
            
            st.download_button(
                label='Download Raw Data',
                data=csv_data,
                file_name=f'earnings_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv'
            )

if __name__ == "__main__":
    main()

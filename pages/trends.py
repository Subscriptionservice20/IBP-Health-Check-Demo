import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import random

# Page configuration
st.set_page_config(page_title="Data Health Trends", page_icon="📈", layout="wide")

# Title
st.title("Supply Chain Data Health Trends")

# Check if connected to SAP
if "connected" not in st.session_state or not st.session_state.connected:
    st.warning("You need to connect to SAP IBP first. Please go to the Home page to establish a connection.")
    st.stop()

# Introduction
st.markdown("""
This page shows how your supply chain master data health metrics have changed over time.
Track improvements, identify deteriorating areas, and understand the impact of data governance initiatives.
""")

# Generate or retrieve trend data
if "trend_data" not in st.session_state:
    # We'd normally fetch this from a historical database
    # For now, we'll simulate it based on current metrics if available
    if "quality_scores" in st.session_state and st.session_state.quality_scores:
        # Generate simulated trend data based on current scores
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        dates = pd.date_range(start=start_date, end=end_date, freq='W')
        
        trend_data = {}
        
        for data_type, current_score in st.session_state.quality_scores.items():
            # Start with a lower score and trend upward to current value
            # with some random variation to simulate real-world fluctuations
            start_score = max(current_score - 2, 0)
            scores = np.linspace(start_score, current_score, len(dates))
            
            # Add some random noise
            np.random.seed(42)  # For reproducibility
            noise = np.random.normal(0, 0.3, len(dates))
            scores = np.clip(scores + noise, 0, 10)
            
            # Create series
            trend_data[data_type] = pd.Series(scores, index=dates)
        
        # Generate dimension-level trends if metrics available
        dimension_trends = {}
        
        if "data_metrics" in st.session_state and st.session_state.data_metrics:
            for dimension in ["completeness", "consistency", "validity", "uniqueness", "timeliness", "accuracy"]:
                dimension_data = {}
                
                for data_type, metrics in st.session_state.data_metrics.items():
                    if dimension in metrics:
                        current_value = metrics[dimension]
                        # Start with a lower score and trend upward
                        start_value = max(current_value - 15, 0)
                        values = np.linspace(start_value, current_value, len(dates))
                        
                        # Add some random noise
                        np.random.seed(int(hash(f"{data_type}-{dimension}")) % 2**32)
                        noise = np.random.normal(0, 3, len(dates))
                        values = np.clip(values + noise, 0, 100)
                        
                        dimension_data[data_type] = pd.Series(values, index=dates)
                
                dimension_trends[dimension] = dimension_data
        
        st.session_state.trend_data = trend_data
        st.session_state.dimension_trends = dimension_trends
    else:
        st.warning("No current data metrics available to generate trend information.")
        st.stop()

# Trend data available
if "trend_data" in st.session_state and st.session_state.trend_data:
    # Time period selection
    st.sidebar.header("Time Range")
    time_range = st.sidebar.selectbox(
        "Select Period",
        ["Last Week", "Last Month", "Last Quarter", "All Available Data"],
        index=2
    )
    
    # Filter data based on time range
    end_date = datetime.now().date()
    if time_range == "Last Week":
        start_date = end_date - timedelta(days=7)
    elif time_range == "Last Month":
        start_date = end_date - timedelta(days=30)
    elif time_range == "Last Quarter":
        start_date = end_date - timedelta(days=90)
    else:
        # Use all available data
        start_date = min([series.index.min() for series in st.session_state.trend_data.values()])
    
    # Filter trend data
    filtered_trends = {}
    for data_type, series in st.session_state.trend_data.items():
        filtered_trends[data_type] = series[series.index >= pd.Timestamp(start_date)]
    
    # Data type selection
    st.sidebar.header("Data Selection")
    data_types = list(filtered_trends.keys())
    selected_data_types = st.sidebar.multiselect(
        "Select Data Types",
        data_types,
        default=data_types[:3] if len(data_types) > 3 else data_types  # Default to first 3 or all if less
    )
    
    # Overall trend chart
    st.header("Overall Data Health Score Trends")
    
    if selected_data_types:
        # Create DataFrame from selected series
        trend_df = pd.DataFrame({data_type: filtered_trends[data_type] for data_type in selected_data_types})
        
        # Add average column if multiple data types selected
        if len(selected_data_types) > 1:
            trend_df["Average"] = trend_df.mean(axis=1)
        
        # Plot the trends
        fig = px.line(
            trend_df,
            x=trend_df.index,
            y=trend_df.columns,
            title="Data Health Score Trends",
            labels={"value": "Quality Score (0-10)", "variable": "Data Type", "index": "Date"},
            markers=True,
            line_shape="spline"
        )
        
        fig.update_layout(
            yaxis=dict(range=[0, 10]),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add interpretation
        if len(selected_data_types) > 0:
            # Calculate improvements
            first_values = trend_df.iloc[0]
            last_values = trend_df.iloc[-1]
            changes = last_values - first_values
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Score Changes")
                
                for data_type in trend_df.columns:
                    change = changes[data_type]
                    if change > 0:
                        st.success(f"**{data_type}**: +{change:.2f} points")
                    elif change < 0:
                        st.error(f"**{data_type}**: {change:.2f} points")
                    else:
                        st.info(f"**{data_type}**: No change")
            
            with col2:
                st.subheader("Current Status")
                
                for data_type in trend_df.columns:
                    score = last_values[data_type]
                    if score >= 8:
                        st.success(f"**{data_type}**: Good ({score:.2f}/10)")
                    elif score >= 6:
                        st.info(f"**{data_type}**: Acceptable ({score:.2f}/10)")
                    elif score >= 4:
                        st.warning(f"**{data_type}**: Needs Improvement ({score:.2f}/10)")
                    else:
                        st.error(f"**{data_type}**: Critical ({score:.2f}/10)")
    else:
        st.info("Please select at least one data type to view trends.")
    
    # Dimension-level trends
    if "dimension_trends" in st.session_state and st.session_state.dimension_trends:
        st.header("Quality Dimension Trends")
        
        # Dimension selection
        dimensions = list(st.session_state.dimension_trends.keys())
        selected_dimension = st.selectbox(
            "Select Quality Dimension",
            dimensions,
            format_func=lambda x: x.capitalize()
        )
        
        if selected_dimension and selected_dimension in st.session_state.dimension_trends:
            dimension_data = st.session_state.dimension_trends[selected_dimension]
            
            # Filter by selected data types and time range
            filtered_dimension_data = {}
            for data_type in selected_data_types:
                if data_type in dimension_data:
                    series = dimension_data[data_type]
                    filtered_dimension_data[data_type] = series[series.index >= pd.Timestamp(start_date)]
            
            if filtered_dimension_data:
                # Create DataFrame
                dimension_df = pd.DataFrame(filtered_dimension_data)
                
                # Plot the trends
                fig = px.line(
                    dimension_df,
                    x=dimension_df.index,
                    y=dimension_df.columns,
                    title=f"{selected_dimension.capitalize()} Trend by Data Type",
                    labels={"value": f"{selected_dimension.capitalize()} (%)", "variable": "Data Type", "index": "Date"},
                    markers=True,
                    line_shape="spline"
                )
                
                fig.update_layout(
                    yaxis=dict(range=[0, 100]),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add improvement metrics
                if not dimension_df.empty:
                    first_values = dimension_df.iloc[0]
                    last_values = dimension_df.iloc[-1]
                    improvements = last_values - first_values
                    
                    st.subheader(f"{selected_dimension.capitalize()} Improvements")
                    
                    improvement_data = []
                    for data_type in dimension_df.columns:
                        improvement = improvements[data_type]
                        current_value = last_values[data_type]
                        improvement_data.append({
                            "Data Type": data_type,
                            "Improvement": f"{improvement:.2f}%",
                            "Current Value": f"{current_value:.2f}%",
                            "Status": "Improved" if improvement > 0 else "Declined" if improvement < 0 else "Unchanged"
                        })
                    
                    improvement_df = pd.DataFrame(improvement_data)
                    st.dataframe(improvement_df, use_container_width=True)
            else:
                st.info("No dimension data available for the selected data types.")
    
    # Historical issues analysis
    st.header("Data Quality Issues History")
    
    # Generate simulated issue history
    if "issue_history" not in st.session_state:
        # We would normally fetch this from a database
        # For now, let's generate some simulated data
        issues_over_time = []
        
        # Use same date range as trend data
        all_dates = list(pd.date_range(start=start_date, end=end_date, freq='W'))
        
        # Issue categories
        issue_categories = [
            "Missing Values", 
            "Invalid Values", 
            "Duplicate Records",
            "Format Inconsistency",
            "Outdated Information"
        ]
        
        # Generate random issue counts that generally decrease over time
        for date in all_dates:
            for data_type in data_types:
                # More issues in the past, fewer in recent dates
                progress_factor = (date - all_dates[0]) / (all_dates[-1] - all_dates[0]) if len(all_dates) > 1 else 0.5
                base_count = max(0, int(50 * (1 - progress_factor)))
                
                for category in issue_categories:
                    # Add some random variation
                    count = max(0, int(base_count * (0.5 + random.random())))
                    
                    if count > 0 or random.random() > 0.7:  # Don't record every zero count
                        issues_over_time.append({
                            "Date": date,
                            "Data Type": data_type,
                            "Issue Category": category,
                            "Issue Count": count
                        })
        
        st.session_state.issue_history = pd.DataFrame(issues_over_time)
    
    # Filter issue history by selected data types and time range
    if "issue_history" in st.session_state:
        filtered_issues = st.session_state.issue_history[
            (st.session_state.issue_history["Date"] >= pd.Timestamp(start_date)) &
            (st.session_state.issue_history["Data Type"].isin(selected_data_types))
        ]
        
        if not filtered_issues.empty:
            # Create issue trend chart
            issue_pivot = filtered_issues.pivot_table(
                index="Date",
                columns=["Data Type", "Issue Category"],
                values="Issue Count",
                aggfunc="sum"
            ).fillna(0)
            
            # Flatten multi-index for plotting
            issue_pivot.columns = [f"{data_type} - {category}" for data_type, category in issue_pivot.columns]
            
            # Aggregate by data type for simplified view
            data_type_totals = filtered_issues.pivot_table(
                index="Date",
                columns="Data Type",
                values="Issue Count",
                aggfunc="sum"
            ).fillna(0)
            
            # Plot the aggregated trends
            fig = px.line(
                data_type_totals,
                x=data_type_totals.index,
                y=data_type_totals.columns,
                title="Total Issues by Data Type",
                labels={"value": "Issue Count", "variable": "Data Type", "index": "Date"},
                markers=True
            )
            
            fig.update_layout(hovermode="x unified")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Issue category breakdown
            st.subheader("Issue Category Breakdown")
            
            # Select data type for category breakdown
            selected_type_for_issues = st.selectbox(
                "Select Data Type for Issue Details",
                selected_data_types
            )
            
            if selected_type_for_issues:
                type_issues = filtered_issues[filtered_issues["Data Type"] == selected_type_for_issues]
                
                if not type_issues.empty:
                    # Pivot to get issue categories over time
                    category_pivot = type_issues.pivot_table(
                        index="Date",
                        columns="Issue Category",
                        values="Issue Count",
                        aggfunc="sum"
                    ).fillna(0)
                    
                    # Plot stacked area chart
                    fig = px.area(
                        category_pivot,
                        x=category_pivot.index,
                        y=category_pivot.columns,
                        title=f"Issue Categories for {selected_type_for_issues}",
                        labels={"value": "Issue Count", "variable": "Issue Category", "index": "Date"}
                    )
                    
                    fig.update_layout(hovermode="x unified")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Issue resolution metrics
                    first_counts = category_pivot.iloc[0].sum()
                    last_counts = category_pivot.iloc[-1].sum()
                    change_pct = (last_counts - first_counts) / first_counts * 100 if first_counts > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Initial Issue Count", 
                            int(first_counts)
                        )
                    
                    with col2:
                        st.metric(
                            "Current Issue Count", 
                            int(last_counts)
                        )
                    
                    with col3:
                        st.metric(
                            "Change", 
                            f"{change_pct:.1f}%",
                            delta=int(last_counts - first_counts),
                            delta_color="inverse"  # Lower is better
                        )
                else:
                    st.info(f"No issue history data available for {selected_type_for_issues}.")
        else:
            st.info("No issue history data available for the selected time period and data types.")
else:
    st.warning("No trend data available. Please sync data and generate data health metrics first.")

# Footer
st.markdown("---")
st.caption(f"Trend analysis generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

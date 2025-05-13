import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(page_title="Supply Chain Data Dashboard", page_icon="📊", layout="wide")

# Title
st.title("Supply Chain Data Health Dashboard")

# Check if connected to SAP and data is available
if "connected" not in st.session_state or not st.session_state.connected:
    st.warning("You need to connect to SAP IBP first. Please go to the Home page to establish a connection.")
    st.stop()

if "quality_scores" not in st.session_state or "data_metrics" not in st.session_state:
    st.info("No data analysis has been performed yet. Please sync data from the Home page.")
    st.stop()

# Dashboard content
st.markdown("""
This dashboard provides an overview of your supply chain master data health metrics. Use the filters below
to customize the view and explore different aspects of your data quality.
""")

# Filter section
st.sidebar.header("Dashboard Filters")

# Filter by data types
if "master_data" in st.session_state and st.session_state.master_data:
    available_data_types = list(st.session_state.master_data.keys())
    selected_data_types = st.sidebar.multiselect(
        "Select Data Types",
        available_data_types,
        default=available_data_types
    )
else:
    selected_data_types = []
    st.warning("No master data available for analysis.")
    st.stop()

# Filter by quality dimensions
quality_dimensions = ["Completeness", "Consistency", "Validity", "Uniqueness", "Timeliness", "Accuracy"]
selected_dimensions = st.sidebar.multiselect(
    "Select Quality Dimensions",
    quality_dimensions,
    default=quality_dimensions
)

# Apply filters to the data
filtered_scores = {}
filtered_metrics = {}

if selected_data_types and "quality_scores" in st.session_state:
    # Filter quality scores
    for data_type in selected_data_types:
        if data_type in st.session_state.quality_scores:
            filtered_scores[data_type] = st.session_state.quality_scores[data_type]
    
    # Filter metrics
    for data_type in selected_data_types:
        if data_type in st.session_state.data_metrics:
            metrics = {}
            for dim in [dim.lower() for dim in selected_dimensions]:
                if dim in st.session_state.data_metrics[data_type]:
                    metrics[dim] = st.session_state.data_metrics[data_type][dim]
            if "issues" in st.session_state.data_metrics[data_type]:
                metrics["issues"] = st.session_state.data_metrics[data_type]["issues"]
            filtered_metrics[data_type] = metrics

# Dashboard layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Overall Data Health Score")
    
    # Calculate average score
    if filtered_scores:
        overall_score = sum(filtered_scores.values()) / len(filtered_scores)
        
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Health Score"},
            gauge={
                'axis': {'range': [0, 10]},
                'bar': {'color': "royalblue"},
                'steps': [
                    {'range': [0, 3], 'color': "red"},
                    {'range': [3, 6], 'color': "orange"},
                    {'range': [6, 8], 'color': "yellow"},
                    {'range': [8, 10], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': overall_score
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add interpretation
        if overall_score < 3:
            st.error("Critical data quality issues. Immediate attention required.")
        elif overall_score < 6:
            st.warning("Significant data quality issues. Action needed.")
        elif overall_score < 8:
            st.info("Moderate data quality. Some improvements needed.")
        else:
            st.success("Good data quality. Continue monitoring.")
    else:
        st.warning("No data available with current filter selection.")

with col2:
    st.subheader("Data Health by Type")
    
    if filtered_scores:
        # Create data for bar chart
        data_types = list(filtered_scores.keys())
        scores = list(filtered_scores.values())
        
        # Create horizontal bar chart
        fig = go.Figure(go.Bar(
            x=scores,
            y=data_types,
            orientation='h',
            marker=dict(
                color=scores,
                colorscale='RdYlGn',
                cmin=0,
                cmax=10
            )
        ))
        
        fig.update_layout(
            xaxis_title="Quality Score (0-10)",
            yaxis_title="Data Type",
            xaxis=dict(range=[0, 10])
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available with current filter selection.")

# Quality dimensions breakdown
st.subheader("Quality Dimensions Breakdown")

if filtered_metrics and selected_dimensions:
    # Prepare data for radar chart
    data_for_radar = {}
    
    for data_type in filtered_metrics:
        metrics = filtered_metrics[data_type]
        data_for_radar[data_type] = {}
        
        for dim in [dim.lower() for dim in selected_dimensions]:
            if dim in metrics:
                # Convert to 0-10 scale for consistency with overall scores
                data_for_radar[data_type][dim.capitalize()] = metrics[dim] / 10
    
    if data_for_radar:
        # Create radar chart
        fig = go.Figure()
        
        dimensions = [dim.capitalize() for dim in selected_dimensions if all(dim.lower() in metrics for metrics in filtered_metrics.values())]
        
        for data_type, values in data_for_radar.items():
            fig.add_trace(go.Scatterpolar(
                r=[values.get(dim, 0) for dim in dimensions],
                theta=dimensions,
                fill='toself',
                name=data_type
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No metrics available for the selected dimensions.")
else:
    st.warning("No data available with current filter selection.")

# Issues table
st.subheader("Data Quality Issues")

if filtered_metrics:
    # Collect all issues
    all_issues = []
    
    for data_type, metrics in filtered_metrics.items():
        if "issues" in metrics:
            for issue in metrics["issues"]:
                issue_with_type = issue.copy()
                issue_with_type["Data Type"] = data_type
                all_issues.append(issue_with_type)
    
    if all_issues:
        # Convert to DataFrame for display
        issues_df = pd.DataFrame(all_issues)
        
        # Add column for impact if it doesn't exist
        if "impact" not in issues_df.columns:
            issues_df["impact"] = "Medium"
        
        # Sort by impact severity
        impact_order = {"High": 0, "Medium": 1, "Low": 2}
        issues_df["impact_order"] = issues_df["impact"].map(impact_order)
        issues_df = issues_df.sort_values("impact_order")
        
        # Display issues with color-coding
        for i, row in issues_df.iterrows():
            impact = row.get("impact", "Medium")
            if impact == "High":
                st.error(f"**{row['Data Type']}** - {row.get('field', '')}: {row.get('issue', 'Issue not specified')}")
            elif impact == "Medium":
                st.warning(f"**{row['Data Type']}** - {row.get('field', '')}: {row.get('issue', 'Issue not specified')}")
            else:
                st.info(f"**{row['Data Type']}** - {row.get('field', '')}: {row.get('issue', 'Issue not specified')}")
    else:
        st.success("No issues detected with the current filter selection.")
else:
    st.warning("No data available with current filter selection.")

# Data completeness by field
st.subheader("Data Completeness by Field")

if "master_data" in st.session_state and selected_data_types:
    # Select data type to analyze
    data_type_for_fields = st.selectbox(
        "Select Data Type for Field Analysis",
        selected_data_types
    )
    
    if data_type_for_fields in st.session_state.master_data:
        data = st.session_state.master_data[data_type_for_fields]
        
        if isinstance(data, pd.DataFrame) and not data.empty:
            # Calculate completeness by field
            completeness = (1 - data.isnull().mean()) * 100
            completeness = completeness.sort_values()
            
            # Plot horizontal bar chart
            fig = px.bar(
                x=completeness.values,
                y=completeness.index,
                orientation='h',
                labels={"x": "Completeness %", "y": "Field"},
                title=f"Field Completeness for {data_type_for_fields}",
                color=completeness.values,
                color_continuous_scale="RdYlGn",
                range_color=[0, 100]
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No data available for {data_type_for_fields}.")
else:
    st.warning("No master data available for analysis.")

# Footer with timestamp
st.markdown("---")
st.caption(f"Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(page_title="Data Health Details", page_icon="🔍", layout="wide")

# Title
st.title("Supply Chain Data Health Details")

# Check if connected to SAP and data is available
if "connected" not in st.session_state or not st.session_state.connected:
    st.warning("You need to connect to SAP IBP first. Please go to the Home page to establish a connection.")
    st.stop()

if "master_data" not in st.session_state or not st.session_state.master_data:
    st.info("No data has been synced yet. Please sync data from the Home page.")
    st.stop()

# Introduction
st.markdown("""
This page provides detailed information about your supply chain master data health.
Explore specific data elements, identify problematic fields, and understand the nature 
of data quality issues affecting your supply chain planning.
""")

# Select data type to analyze
data_types = list(st.session_state.master_data.keys())
selected_data_type = st.selectbox("Select Data Type to Analyze", data_types)

if selected_data_type and selected_data_type in st.session_state.master_data:
    data = st.session_state.master_data[selected_data_type]
    
    if not isinstance(data, pd.DataFrame) or data.empty:
        st.warning(f"No data available for {selected_data_type}.")
        st.stop()
    
    # Data overview
    st.header("Data Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Records", len(data))
    
    with col2:
        st.metric("Fields", len(data.columns))
    
    with col3:
        null_count = data.isnull().sum().sum()
        total_cells = data.size
        null_percentage = (null_count / total_cells) * 100 if total_cells > 0 else 0
        st.metric("Missing Values", f"{null_count} ({null_percentage:.1f}%)")
    
    with col4:
        # Get quality score if available
        if "quality_scores" in st.session_state and selected_data_type in st.session_state.quality_scores:
            quality_score = st.session_state.quality_scores[selected_data_type]
            st.metric("Quality Score", f"{quality_score:.1f}/10")
        else:
            st.metric("Quality Score", "N/A")
    
    # Data sample
    with st.expander("Data Sample", expanded=False):
        st.dataframe(data.head(10), use_container_width=True)
    
    # Completeness analysis
    st.header("Field Completeness Analysis")
    
    # Create completeness heatmap
    completeness_data = (1 - data.isnull().mean()) * 100
    completeness_df = pd.DataFrame({
        'Field': completeness_data.index,
        'Completeness (%)': completeness_data.values
    })
    completeness_df = completeness_df.sort_values('Completeness (%)', ascending=True)
    
    fig = px.bar(
        completeness_df,
        x='Completeness (%)',
        y='Field',
        orientation='h',
        color='Completeness (%)',
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        title="Field Completeness"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Fields with lowest completeness
    low_completeness = completeness_df[completeness_df['Completeness (%)'] < 90]
    if not low_completeness.empty:
        st.warning("Fields with completeness below 90%:")
        st.dataframe(low_completeness, use_container_width=True)
    else:
        st.success("All fields have at least 90% completeness.")
    
    # Data type distribution
    st.header("Data Type Distribution")
    
    # Create a table of data types
    data_types_dict = {}
    for column in data.columns:
        dtype = str(data[column].dtype)
        if dtype in data_types_dict:
            data_types_dict[dtype].append(column)
        else:
            data_types_dict[dtype] = [column]
    
    # Display data types
    dtype_data = []
    for dtype, columns in data_types_dict.items():
        dtype_data.append({
            "Data Type": dtype,
            "Count": len(columns),
            "Fields": ", ".join(columns[:5]) + ("..." if len(columns) > 5 else "")
        })
    
    st.dataframe(pd.DataFrame(dtype_data), use_container_width=True)
    
    # Value distribution for selected field
    st.header("Value Distribution Analysis")
    
    # Let user select a field
    selected_field = st.selectbox(
        "Select a field to analyze its value distribution",
        data.columns.tolist()
    )
    
    if selected_field:
        field_data = data[selected_field]
        null_count = field_data.isnull().sum()
        non_null_count = len(field_data) - null_count
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Non-null Values", non_null_count)
        
        with col2:
            st.metric("Null Values", null_count)
        
        with col3:
            # Calculate uniqueness
            if non_null_count > 0:
                unique_values = field_data.nunique()
                uniqueness_pct = (unique_values / non_null_count) * 100
                st.metric("Unique Values", f"{unique_values} ({uniqueness_pct:.1f}%)")
            else:
                st.metric("Unique Values", "0 (0.0%)")
        
        with col4:
            # Display data type
            st.metric("Data Type", str(field_data.dtype))
        
        # Display distribution based on data type
        if pd.api.types.is_numeric_dtype(field_data):
            # For numeric fields, show histogram and statistics
            fig = px.histogram(
                field_data.dropna(),
                title=f"Distribution of {selected_field}",
                labels={"value": selected_field, "count": "Frequency"},
                color_discrete_sequence=["royalblue"]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show statistics
            if non_null_count > 0:
                stats = field_data.describe()
                st.dataframe(stats, use_container_width=True)
                
                # Check for outliers
                q1 = stats['25%']
                q3 = stats['75%']
                iqr = q3 - q1
                lower_bound = q1 - (1.5 * iqr)
                upper_bound = q3 + (1.5 * iqr)
                
                outliers = field_data[(field_data < lower_bound) | (field_data > upper_bound)]
                outlier_percentage = len(outliers) / non_null_count * 100
                
                if len(outliers) > 0:
                    st.warning(f"Found {len(outliers)} outliers ({outlier_percentage:.1f}% of non-null values) based on IQR method.")
        
        elif pd.api.types.is_string_dtype(field_data):
            # For string fields, show value counts
            value_counts = field_data.value_counts().reset_index().head(20)
            value_counts.columns = [selected_field, 'Count']
            
            fig = px.bar(
                value_counts,
                x=selected_field,
                y='Count',
                title=f"Top 20 values for {selected_field}",
                color='Count',
                color_continuous_scale="Blues"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Additional string analysis
            if non_null_count > 0:
                # Length statistics
                field_data_non_null = field_data.dropna().astype(str)
                lengths = field_data_non_null.str.len()
                
                length_stats = {
                    "Min Length": lengths.min(),
                    "Max Length": lengths.max(),
                    "Avg Length": lengths.mean(),
                    "Empty Strings": (field_data_non_null == "").sum()
                }
                
                st.dataframe(pd.Series(length_stats, name="String Metrics"), use_container_width=True)
        
        elif pd.api.types.is_datetime64_any_dtype(field_data):
            # For datetime fields, show timeline visualization
            if non_null_count > 0:
                date_counts = field_data.dropna().dt.date.value_counts().sort_index()
                date_df = pd.DataFrame({
                    'Date': date_counts.index,
                    'Count': date_counts.values
                })
                
                fig = px.line(
                    date_df,
                    x='Date',
                    y='Count',
                    title=f"Timeline distribution of {selected_field}",
                    markers=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Date range information
                date_range = {
                    "Earliest Date": field_data.min(),
                    "Latest Date": field_data.max(),
                    "Date Range (days)": (field_data.max() - field_data.min()).days if pd.notna(field_data.min()) and pd.notna(field_data.max()) else "N/A"
                }
                
                st.dataframe(pd.Series(date_range, name="Date Metrics"), use_container_width=True)
        
        else:
            # For other types, show basic value counts
            value_counts = field_data.value_counts().head(10)
            st.bar_chart(value_counts)
    
    # Data quality issues
    st.header("Identified Data Quality Issues")
    
    if "data_metrics" in st.session_state and selected_data_type in st.session_state.data_metrics:
        metrics = st.session_state.data_metrics[selected_data_type]
        
        if "issues" in metrics and metrics["issues"]:
            # Convert issues to DataFrame
            issues_df = pd.DataFrame(metrics["issues"])
            
            # Add severity color
            def get_severity_color(impact):
                if impact == "High":
                    return "red"
                elif impact == "Medium":
                    return "orange"
                else:
                    return "blue"
            
            # Display issues with color-coding
            for i, row in issues_df.iterrows():
                impact = row.get("impact", "Medium")
                field = row.get("field", "General")
                issue = row.get("issue", "Issue not specified")
                
                if impact == "High":
                    st.error(f"**{field}**: {issue}")
                elif impact == "Medium":
                    st.warning(f"**{field}**: {issue}")
                else:
                    st.info(f"**{field}**: {issue}")
        else:
            st.success("No specific data quality issues identified.")
    else:
        st.info("No data quality analysis available. Please sync data and analyze data health metrics.")
    
    # Improvement recommendations
    st.header("Improvement Recommendations")
    
    # Generate recommendations based on data analysis
    recommendations = []
    
    # Completeness recommendations
    low_completeness_fields = completeness_df[completeness_df['Completeness (%)'] < 95]['Field'].tolist()
    if low_completeness_fields:
        recommendations.append({
            "Category": "Completeness",
            "Recommendation": f"Improve data completeness for fields: {', '.join(low_completeness_fields[:5])}{'...' if len(low_completeness_fields) > 5 else ''}",
            "Priority": "High" if any(completeness_df[completeness_df['Field'].isin(low_completeness_fields)]['Completeness (%)'] < 80) else "Medium"
        })
    
    # Add data type specific recommendations
    if selected_data_type == "Products":
        # Check for product categorization
        if "ProductCategory" in data.columns and data["ProductCategory"].isnull().mean() > 0.1:
            recommendations.append({
                "Category": "Classification",
                "Recommendation": "Improve product categorization to support better planning segmentation",
                "Priority": "Medium"
            })
        
        # Check for unit of measure consistency
        if "UnitOfMeasure" in data.columns and data["UnitOfMeasure"].nunique() > 5:
            recommendations.append({
                "Category": "Standardization",
                "Recommendation": "Standardize units of measure to reduce conversion errors in planning",
                "Priority": "Medium"
            })
    
    elif selected_data_type == "Locations":
        # Check for location hierarchy
        if "ParentLocation" in data.columns and data["ParentLocation"].isnull().mean() > 0.2:
            recommendations.append({
                "Category": "Hierarchy",
                "Recommendation": "Complete location hierarchy information to support multi-echelon planning",
                "Priority": "High"
            })
    
    # Generic recommendations
    if data.select_dtypes(include=['object']).columns.any():
        recommendations.append({
            "Category": "Data Typing",
            "Recommendation": "Review string fields for potential data type standardization",
            "Priority": "Low"
        })
    
    # Display recommendations
    if recommendations:
        # Convert to DataFrame
        recommendations_df = pd.DataFrame(recommendations)
        
        # Display with color-coding
        for i, row in recommendations_df.iterrows():
            priority = row["Priority"]
            category = row["Category"]
            recommendation = row["Recommendation"]
            
            if priority == "High":
                st.error(f"**{category}**: {recommendation} (Priority: {priority})")
            elif priority == "Medium":
                st.warning(f"**{category}**: {recommendation} (Priority: {priority})")
            else:
                st.info(f"**{category}**: {recommendation} (Priority: {priority})")
    else:
        st.success("No specific improvement recommendations at this time. Data appears to be in good health.")

# Footer
st.markdown("---")
st.caption(f"Data analysis performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

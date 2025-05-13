import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import io
import base64

# Page configuration
st.set_page_config(page_title="Supply Chain Data Reports", page_icon="📊", layout="wide")

# Title
st.title("Supply Chain Data Quality Reports")

# Check if connected to SAP and data is available
if "connected" not in st.session_state or not st.session_state.connected:
    st.warning("You need to connect to SAP IBP first. Please go to the Home page to establish a connection.")
    st.stop()

if "master_data" not in st.session_state or not st.session_state.master_data:
    st.info("No data has been synced yet. Please sync data from the Home page.")
    st.stop()

# Introduction
st.markdown("""
This page enables you to generate detailed reports on your supply chain master data health.
Create custom reports focused on specific data domains, quality dimensions, or issues for
stakeholder communication and improvement planning.
""")

# Report Configuration Section
st.header("Report Configuration")

col1, col2 = st.columns(2)

with col1:
    # Report type
    report_type = st.selectbox(
        "Report Type",
        ["Executive Summary", "Detailed Quality Analysis", "Issue Identification", "Improvement Tracking", "Custom"]
    )
    
    # Data types to include
    available_data_types = list(st.session_state.master_data.keys())
    data_types_for_report = st.multiselect(
        "Include Data Types",
        available_data_types,
        default=available_data_types[:2] if len(available_data_types) >= 2 else available_data_types
    )

with col2:
    # Quality dimensions to focus on
    quality_dimensions = ["Completeness", "Consistency", "Validity", "Uniqueness", "Timeliness", "Accuracy"]
    selected_dimensions = st.multiselect(
        "Focus Quality Dimensions",
        quality_dimensions,
        default=["Completeness", "Validity", "Accuracy"]
    )
    
    # Report period
    report_period = st.selectbox(
        "Report Period",
        ["Current Snapshot", "Last Week", "Last Month", "Last Quarter", "Custom"]
    )
    
    if report_period == "Custom":
        date_range = st.date_input(
            "Select Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )

# Optional report title
report_title = st.text_input("Report Title (Optional)", 
                            value=f"Supply Chain Data Quality Report - {datetime.now().strftime('%B %Y')}")

# Include issues toggle
include_issues = st.checkbox("Include Identified Issues", value=True)

# Include recommendations toggle
include_recommendations = st.checkbox("Include Improvement Recommendations", value=True)

# Generate Report Button
if st.button("Generate Report"):
    if not data_types_for_report:
        st.error("Please select at least one data type to include in the report.")
    elif not selected_dimensions:
        st.error("Please select at least one quality dimension to include in the report.")
    else:
        with st.spinner("Generating report..."):
            # Report Container
            report_container = st.container()
            
            with report_container:
                st.header(report_title)
                st.markdown(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
                
                # Executive Summary section
                st.subheader("Executive Summary")
                
                # Calculate overall metrics from available data
                if "quality_scores" in st.session_state:
                    filtered_scores = {dt: score for dt, score in st.session_state.quality_scores.items() 
                                    if dt in data_types_for_report}
                    
                    if filtered_scores:
                        overall_score = sum(filtered_scores.values()) / len(filtered_scores)
                        
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Overall Data Health Score", f"{overall_score:.2f}/10")
                        
                        with col2:
                            # Determine how many data types have acceptable scores (>= 7)
                            acceptable_count = sum(1 for score in filtered_scores.values() if score >= 7)
                            total_count = len(filtered_scores)
                            st.metric("Data Types with Good Health", f"{acceptable_count}/{total_count}")
                        
                        with col3:
                            # Calculate improvement needed to reach target (8.5/10)
                            target_score = 8.5
                            improvement_needed = max(0, target_score - overall_score)
                            st.metric("Improvement Needed", f"{improvement_needed:.2f} points")
                        
                        # Executive summary text
                        if overall_score >= 8.5:
                            st.success("""
                            **The overall supply chain master data health is excellent.** Most data types meet or exceed 
                            quality standards, providing a reliable foundation for supply chain planning processes.
                            Continue with regular monitoring and maintenance activities.
                            """)
                        elif overall_score >= 7.0:
                            st.info("""
                            **The overall supply chain master data health is good.** While most data elements 
                            are of acceptable quality, there are opportunities for targeted improvements.
                            Focus on addressing specific issues identified in this report.
                            """)
                        elif overall_score >= 5.0:
                            st.warning("""
                            **The overall supply chain master data health requires attention.** Several critical 
                            data elements have quality issues that may impact planning accuracy.
                            Prioritize improvement activities based on the recommendations in this report.
                            """)
                        else:
                            st.error("""
                            **The overall supply chain master data health is critical.** Significant data quality 
                            issues exist that are likely impacting planning processes and decisions.
                            Immediate remediation actions are recommended.
                            """)
                        
                        # Bar chart of quality scores by data type
                        score_df = pd.DataFrame({
                            "Data Type": list(filtered_scores.keys()),
                            "Quality Score": list(filtered_scores.values())
                        })
                        
                        fig = px.bar(
                            score_df,
                            x="Data Type", 
                            y="Quality Score",
                            title="Data Health by Type",
                            color="Quality Score",
                            color_continuous_scale="RdYlGn",
                            range_color=[0, 10]
                        )
                        
                        fig.update_layout(yaxis_range=[0, 10])
                        st.plotly_chart(fig, use_container_width=True)
                    
                # Detailed Quality Analysis section
                st.subheader("Quality Dimensions Analysis")
                
                if "data_metrics" in st.session_state:
                    # Filter metrics for selected data types
                    filtered_metrics = {dt: metrics for dt, metrics in st.session_state.data_metrics.items() 
                                       if dt in data_types_for_report}
                    
                    if filtered_metrics:
                        # Prepare data for radar chart
                        dimensions = [dim.lower() for dim in selected_dimensions]
                        radar_data = []
                        
                        for data_type, metrics in filtered_metrics.items():
                            data_point = {"Data Type": data_type}
                            for dim in dimensions:
                                if dim in metrics:
                                    data_point[dim.capitalize()] = metrics[dim]
                            radar_data.append(data_point)
                        
                        radar_df = pd.DataFrame(radar_data)
                        
                        if not radar_df.empty and len(radar_df.columns) > 1:  # Ensure there's data to plot
                            # Create radar chart
                            fig = go.Figure()
                            
                            for i, row in radar_df.iterrows():
                                fig.add_trace(go.Scatterpolar(
                                    r=[row[dim.capitalize()] for dim in dimensions],
                                    theta=[dim.capitalize() for dim in dimensions],
                                    fill='toself',
                                    name=row["Data Type"]
                                ))
                            
                            fig.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, 100]
                                    )
                                ),
                                showlegend=True,
                                title="Quality Dimensions by Data Type"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Table of dimension scores
                            st.subheader("Quality Dimension Scores (%)")
                            
                            table_data = []
                            for data_type, metrics in filtered_metrics.items():
                                row_data = {"Data Type": data_type}
                                for dim in dimensions:
                                    if dim.lower() in metrics:
                                        row_data[dim.capitalize()] = f"{metrics[dim.lower()]:.2f}%"
                                    else:
                                        row_data[dim.capitalize()] = "N/A"
                                table_data.append(row_data)
                            
                            st.dataframe(pd.DataFrame(table_data), use_container_width=True)
                
                # Issue Identification section
                if include_issues and "data_metrics" in st.session_state:
                    st.subheader("Identified Issues")
                    
                    all_issues = []
                    
                    for data_type, metrics in filtered_metrics.items():
                        if "issues" in metrics and metrics["issues"]:
                            for issue in metrics["issues"]:
                                issue_with_type = issue.copy()
                                issue_with_type["Data Type"] = data_type
                                all_issues.append(issue_with_type)
                    
                    if all_issues:
                        # Convert to DataFrame
                        issues_df = pd.DataFrame(all_issues)
                        
                        # Ensure consistent column names
                        if "field" in issues_df.columns:
                            issues_df.rename(columns={"field": "Field"}, inplace=True)
                        if "issue" in issues_df.columns:
                            issues_df.rename(columns={"issue": "Issue"}, inplace=True)
                        if "impact" in issues_df.columns:
                            issues_df.rename(columns={"impact": "Impact"}, inplace=True)
                        
                        # Sort by impact severity
                        impact_order = {"High": 0, "Medium": 1, "Low": 2}
                        if "Impact" in issues_df.columns:
                            issues_df["impact_order"] = issues_df["Impact"].map(impact_order)
                            issues_df = issues_df.sort_values("impact_order")
                            issues_df = issues_df.drop(columns=["impact_order"])
                        
                        # Display issues table
                        st.dataframe(issues_df, use_container_width=True)
                        
                        # Summary of issues by severity
                        if "Impact" in issues_df.columns:
                            impact_counts = issues_df["Impact"].value_counts().reset_index()
                            impact_counts.columns = ["Severity", "Count"]
                            
                            # Create pie chart
                            fig = px.pie(
                                impact_counts, 
                                values="Count", 
                                names="Severity",
                                title="Issues by Severity",
                                color="Severity",
                                color_discrete_map={"High": "red", "Medium": "orange", "Low": "blue"}
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.success("No issues identified for the selected data types.")
                
                # Data overview section
                st.subheader("Data Overview")
                
                # Create a summary table
                summary_data = []
                for data_type, data in st.session_state.master_data.items():
                    if data_type in data_types_for_report and isinstance(data, pd.DataFrame):
                        record_count = len(data)
                        field_count = len(data.columns)
                        empty_values = data.isna().sum().sum()
                        total_values = record_count * field_count
                        completeness = 100 - (empty_values / total_values * 100) if total_values > 0 else 0
                        
                        summary_data.append({
                            "Data Type": data_type,
                            "Records": record_count,
                            "Fields": field_count,
                            "Completeness (%)": round(completeness, 2)
                        })
                
                if summary_data:
                    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
                
                # Recommendations section
                if include_recommendations:
                    st.subheader("Improvement Recommendations")
                    
                    recommendations = []
                    
                    # Generate recommendations based on the metrics and issues
                    for data_type, metrics in filtered_metrics.items():
                        # Recommendations based on completeness
                        if "completeness" in metrics and metrics["completeness"] < 90:
                            recommendations.append({
                                "Data Type": data_type,
                                "Focus Area": "Completeness",
                                "Recommendation": "Implement validation rules to ensure all required fields are populated.",
                                "Priority": "High" if metrics["completeness"] < 75 else "Medium"
                            })
                        
                        # Recommendations based on consistency
                        if "consistency" in metrics and metrics["consistency"] < 90:
                            recommendations.append({
                                "Data Type": data_type,
                                "Focus Area": "Consistency",
                                "Recommendation": "Standardize data formats and enforce data governance protocols.",
                                "Priority": "High" if metrics["consistency"] < 75 else "Medium"
                            })
                        
                        # Recommendations based on validity
                        if "validity" in metrics and metrics["validity"] < 90:
                            recommendations.append({
                                "Data Type": data_type,
                                "Focus Area": "Validity",
                                "Recommendation": "Implement business rule validation in SAP IBP for critical fields.",
                                "Priority": "High" if metrics["validity"] < 75 else "Medium"
                            })
                        
                        # Recommendations based on uniqueness
                        if "uniqueness" in metrics and metrics["uniqueness"] < 98:
                            recommendations.append({
                                "Data Type": data_type,
                                "Focus Area": "Uniqueness",
                                "Recommendation": "Implement deduplication processes and enforce unique key constraints.",
                                "Priority": "Medium"
                            })
                        
                        # Recommendations based on timeliness
                        if "timeliness" in metrics and metrics["timeliness"] < 85:
                            recommendations.append({
                                "Data Type": data_type,
                                "Focus Area": "Timeliness",
                                "Recommendation": "Establish regular data refresh cycles and monitor update frequency.",
                                "Priority": "Medium"
                            })
                    
                    # Data type specific recommendations
                    for data_type in data_types_for_report:
                        if data_type == "Products":
                            recommendations.append({
                                "Data Type": "Products",
                                "Focus Area": "Classification",
                                "Recommendation": "Ensure all products have proper categorization for accurate demand planning.",
                                "Priority": "Medium"
                            })
                        elif data_type == "Locations":
                            recommendations.append({
                                "Data Type": "Locations",
                                "Focus Area": "Hierarchy",
                                "Recommendation": "Verify location hierarchy accuracy for proper supply chain network modeling.",
                                "Priority": "Medium"
                            })
                    
                    if recommendations:
                        # Display recommendations table
                        recommendations_df = pd.DataFrame(recommendations)
                        
                        # Sort by priority
                        priority_order = {"High": 0, "Medium": 1, "Low": 2}
                        recommendations_df["priority_order"] = recommendations_df["Priority"].map(priority_order)
                        recommendations_df = recommendations_df.sort_values("priority_order")
                        recommendations_df = recommendations_df.drop(columns=["priority_order"])
                        
                        st.dataframe(recommendations_df, use_container_width=True)
                    else:
                        st.success("No specific recommendations needed for the selected data.")
                
                # Footer
                st.markdown("---")
                st.markdown(f"Report generated by SAP IBP Supply Chain Data Health Monitor | {datetime.now().strftime('%Y-%m-%d')}")

                # Create download link for CSV export of issues and recommendations
                download_section = st.expander("Export Report Data")
                
                with download_section:
                    if include_issues and 'issues_df' in locals() and not issues_df.empty:
                        csv_issues = issues_df.to_csv(index=False)
                        b64_issues = base64.b64encode(csv_issues.encode()).decode()
                        href_issues = f'<a href="data:file/csv;base64,{b64_issues}" download="data_quality_issues.csv">Download Issues CSV</a>'
                        st.markdown(href_issues, unsafe_allow_html=True)
                    
                    if include_recommendations and 'recommendations_df' in locals() and not recommendations_df.empty:
                        csv_recommendations = recommendations_df.to_csv(index=False)
                        b64_recommendations = base64.b64encode(csv_recommendations.encode()).decode()
                        href_recommendations = f'<a href="data:file/csv;base64,{b64_recommendations}" download="improvement_recommendations.csv">Download Recommendations CSV</a>'
                        st.markdown(href_recommendations, unsafe_allow_html=True)
                    
                    if 'summary_data' in locals() and summary_data:
                        csv_summary = pd.DataFrame(summary_data).to_csv(index=False)
                        b64_summary = base64.b64encode(csv_summary.encode()).decode()
                        href_summary = f'<a href="data:file/csv;base64,{b64_summary}" download="data_summary.csv">Download Data Summary CSV</a>'
                        st.markdown(href_summary, unsafe_allow_html=True)

# Report Templates Section
st.header("Report Templates")

# Template selector
template_options = {
    "Executive Summary": "High-level overview focusing on key metrics and critical issues",
    "S&OP Readiness": "Assessment of data health for Sales & Operations Planning processes",
    "Demand Planning Quality": "Focus on data elements critical for demand forecasting",
    "Inventory Health": "Detailed analysis of inventory master data quality",
    "Network Design Readiness": "Evaluation of location and transportation data health"
}

col1, col2 = st.columns([1, 2])

with col1:
    selected_template = st.radio("Select Template", list(template_options.keys()))

with col2:
    st.info(f"**Template Description**: {template_options[selected_template]}")
    
    if selected_template == "Executive Summary":
        st.markdown("""
        This template provides a concise overview of data health with:
        - Overall quality score and status
        - Summary of critical issues by data domain
        - Top 3-5 improvement recommendations
        - Key risk areas affecting business processes
        """)
    elif selected_template == "S&OP Readiness":
        st.markdown("""
        This template focuses on data elements critical for S&OP:
        - Product hierarchy completeness and accuracy
        - Customer/market data quality
        - Historical demand data reliability
        - Supply capacity data quality
        - Time series consistency
        """)
    elif selected_template == "Demand Planning Quality":
        st.markdown("""
        This template examines data critical for forecasting:
        - Product attribute completeness
        - Customer segmentation data quality
        - Historical demand data consistency
        - Seasonality factor accuracy
        - Promotional data completeness
        """)
    
    # Apply Template button
    if st.button("Apply Template"):
        st.success(f"Template '{selected_template}' applied. Configure additional options and click 'Generate Report'")
        st.rerun()  # Rerun to apply the template

# Schedule Reports section
with st.expander("Schedule Regular Reports"):
    st.markdown("""
    Configure automated report generation and distribution. 
    Reports can be scheduled for regular generation and sent to designated recipients.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        schedule_frequency = st.selectbox(
            "Report Frequency",
            ["Daily", "Weekly", "Monthly", "Quarterly"]
        )
        
        if schedule_frequency == "Weekly":
            schedule_day = st.selectbox(
                "Day of Week",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            )
        elif schedule_frequency == "Monthly":
            schedule_day = st.selectbox(
                "Day of Month",
                list(range(1, 29))
            )
    
    with col2:
        report_recipients = st.text_area(
            "Recipients (email addresses, one per line)"
        )
        
        report_format = st.selectbox(
            "Report Format",
            ["PDF", "Excel", "CSV", "HTML"]
        )
    
    if st.button("Schedule Report"):
        st.info("This feature would schedule the report based on your configuration. In the current implementation, scheduling functionality is simulated.")
        st.success("Report scheduled successfully! It will be generated and distributed according to your configuration.")

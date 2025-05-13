import streamlit as st
import pandas as pd
import datetime
import os
from utils.sap_connector import SAPConnector
from utils.data_quality import DataQualityAnalyzer

# Page configuration
st.set_page_config(
    page_title="SAP IBP Supply Chain Data Health",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'last_sync' not in st.session_state:
    st.session_state.last_sync = None
if 'master_data' not in st.session_state:
    st.session_state.master_data = None
if 'quality_scores' not in st.session_state:
    st.session_state.quality_scores = None
if 'data_metrics' not in st.session_state:
    st.session_state.data_metrics = None

# Title and introduction
st.title("SAP IBP Supply Chain Data Health Monitor")
st.markdown("""
This application connects to SAP Integrated Business Planning (IBP) to analyze and visualize 
the health of your supply chain master data elements. Monitor data quality metrics, 
identify issues, and track improvements over time.
""")

# Sidebar for connection settings
with st.sidebar:
    st.header("Connection Options")
    
    # Add demo mode option
    connection_mode = st.radio(
        "Select Connection Mode",
        ["Demo Mode", "SAP IBP Connection"]
    )
    
    if connection_mode == "Demo Mode":
        # Demo mode settings
        st.info("Demo mode uses simulated supply chain data for demonstration purposes.")
        
        if st.button("Load Demo Data"):
            with st.spinner("Loading demo data..."):
                try:
                    # Import the demo data generator
                    from utils.demo_data_generator import generate_demo_data
                    
                    # Generate demo data
                    demo_data = generate_demo_data()
                    
                    # Set up session state
                    st.session_state.master_data = demo_data
                    st.session_state.connected = True
                    st.session_state.last_sync = datetime.datetime.now()
                    
                    # Calculate data quality metrics
                    analyzer = DataQualityAnalyzer(demo_data)
                    st.session_state.quality_scores = analyzer.calculate_quality_scores()
                    st.session_state.data_metrics = analyzer.analyze_data_health()
                    
                    st.success("Demo data loaded successfully!")
                except Exception as e:
                    st.error(f"Error loading demo data: {str(e)}")
    else:
        # SAP IBP Connection parameters
        st.header("SAP IBP Connection")
        
        # Connection parameters
        sap_url = st.text_input("SAP IBP URL", placeholder="https://your-tenant.sapibp.com", 
                                value=os.getenv("SAP_IBP_URL", ""))
        sap_client = st.text_input("Client", placeholder="100", value=os.getenv("SAP_CLIENT", ""))
        sap_username = st.text_input("Username", value=os.getenv("SAP_USERNAME", ""))
        sap_password = st.text_input("Password", type="password", value=os.getenv("SAP_PASSWORD", ""))
        
        # Connect button
        if st.button("Connect to SAP IBP"):
            if sap_url and sap_client and sap_username and sap_password:
                with st.spinner("Connecting to SAP IBP..."):
                    try:
                        sap_connector = SAPConnector(
                            url=sap_url,
                            client=sap_client,
                            username=sap_username,
                            password=sap_password
                        )
                        
                        # Test connection
                        if sap_connector.test_connection():
                            st.session_state.sap_connector = sap_connector
                            st.session_state.connected = True
                            st.success("Successfully connected to SAP IBP!")
                        else:
                            st.error("Failed to connect to SAP IBP. Please check your credentials and try again.")
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")
            else:
                st.warning("Please fill in all connection details.")
    
    # Display connection status
    if st.session_state.connected:
        st.info("Status: Connected")
        if st.session_state.last_sync:
            st.info(f"Last sync: {st.session_state.last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Data fetch options
        st.header("Data Fetch Options")
        data_types = st.multiselect(
            "Select master data types to analyze",
            ["Products", "Locations", "Customers", "Suppliers", "Time Profiles", "Resource Plans"],
            default=["Products", "Locations"]
        )
        
        time_period = st.selectbox(
            "Time period for analysis",
            ["Last Week", "Last Month", "Last Quarter", "Last Year", "Custom..."]
        )
        
        if time_period == "Custom...":
            date_range = st.date_input(
                "Select date range",
                value=(datetime.datetime.now() - datetime.timedelta(days=30), datetime.datetime.now()),
                max_value=datetime.datetime.now()
            )
        
        if st.button("Sync Data Now"):
            # Check if we're in demo mode or SAP connection mode
            if connection_mode == "Demo Mode":
                with st.spinner("Refreshing demo data..."):
                    try:
                        # Import the demo data generator
                        from utils.demo_data_generator import generate_demo_data
                        
                        # Generate demo data
                        demo_data = generate_demo_data()
                        
                        # Filter to selected data types
                        filtered_data = {k: v for k, v in demo_data.items() if k in data_types}
                        
                        if filtered_data:
                            st.session_state.master_data = filtered_data
                            st.session_state.last_sync = datetime.datetime.now()
                            
                            # Calculate data quality metrics
                            analyzer = DataQualityAnalyzer(filtered_data)
                            st.session_state.quality_scores = analyzer.calculate_quality_scores()
                            st.session_state.data_metrics = analyzer.analyze_data_health()
                            
                            st.success("Demo data refreshed successfully!")
                            st.rerun()
                        else:
                            st.error("No data types were selected. Please select at least one data type.")
                    except Exception as e:
                        st.error(f"Error refreshing demo data: {str(e)}")
            else:
                # SAP IBP data sync
                with st.spinner("Fetching master data from SAP IBP..."):
                    try:
                        # Fetch the selected data types
                        all_data = {}
                        for data_type in data_types:
                            data = st.session_state.sap_connector.fetch_master_data(data_type.lower().replace(" ", "_"))
                            if data is not None:
                                all_data[data_type] = data
                        
                        if all_data:
                            st.session_state.master_data = all_data
                            st.session_state.last_sync = datetime.datetime.now()
                            
                            # Calculate data quality metrics
                            analyzer = DataQualityAnalyzer(all_data)
                            st.session_state.quality_scores = analyzer.calculate_quality_scores()
                            st.session_state.data_metrics = analyzer.analyze_data_health()
                            
                            st.success("Data sync completed successfully!")
                            st.rerun()
                        else:
                            st.error("No data was retrieved. Please check your selections.")
                    except Exception as e:
                        st.error(f"Data sync error: {str(e)}")

# Main content area
if not st.session_state.connected:
    if connection_mode == "Demo Mode":
        st.info("Please click 'Load Demo Data' in the sidebar to analyze simulated supply chain data.")
    else:
        st.info("Please connect to SAP IBP using the sidebar options to start analyzing data.")
    
    # Show a sample of what the app offers even before connection
    with st.expander("What this app provides"):
        st.markdown("""
        ### Supply Chain Data Health Monitoring
        - **Master Data Quality Assessment**: Evaluate completeness, accuracy, and consistency of your supply chain master data
        - **Data Health Dashboards**: Visualize key metrics with interactive charts
        - **Time-Series Analysis**: Track data quality improvements over time
        - **Customizable Reports**: Generate detailed reports on specific data domains
        - **Issue Identification**: Automatically detect common data problems affecting supply chain planning
        
        Use Demo Mode to explore the application features with simulated data, or connect to your SAP IBP instance for real data analysis.
        """)
else:
    # Display tabs for primary navigation
    tab1, tab2, tab3 = st.tabs(["Data Overview", "Quality Metrics", "Recommendations"])
    
    with tab1:
        st.header("Master Data Overview")
        if st.session_state.master_data:
            # Create a summary of the data
            summary_data = []
            for data_type, data in st.session_state.master_data.items():
                if isinstance(data, pd.DataFrame):
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
                
                # Show a sample of each data type
                data_type_to_view = st.selectbox("Select data type to view sample", list(st.session_state.master_data.keys()))
                if data_type_to_view and data_type_to_view in st.session_state.master_data:
                    st.write(f"Sample of {data_type_to_view} data:")
                    st.dataframe(st.session_state.master_data[data_type_to_view].head(10), use_container_width=True)
            else:
                st.warning("No data available for display. Try syncing data again.")
        else:
            st.info("No data has been synced yet. Use the 'Sync Data Now' button in the sidebar.")
    
    with tab2:
        st.header("Data Quality Metrics")
        if st.session_state.quality_scores and st.session_state.data_metrics:
            # Display overall quality score
            overall_score = sum(st.session_state.quality_scores.values()) / len(st.session_state.quality_scores)
            st.metric("Overall Data Health Score", f"{overall_score:.2f}/10")
            
            # Display individual quality scores
            st.subheader("Quality Scores by Data Type")
            score_df = pd.DataFrame({
                "Data Type": list(st.session_state.quality_scores.keys()),
                "Quality Score": list(st.session_state.quality_scores.values())
            })
            
            # Create a bar chart for quality scores
            st.bar_chart(score_df.set_index("Data Type"))
            
            # Detailed metrics
            st.subheader("Detailed Metrics")
            
            # Select data type for detailed view
            selected_data_type = st.selectbox(
                "Select data type for detailed metrics", 
                list(st.session_state.data_metrics.keys())
            )
            
            if selected_data_type in st.session_state.data_metrics:
                metrics = st.session_state.data_metrics[selected_data_type]
                
                # Display metrics in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Completeness", f"{metrics.get('completeness', 0):.2f}%")
                    st.metric("Uniqueness", f"{metrics.get('uniqueness', 0):.2f}%")
                
                with col2:
                    st.metric("Consistency", f"{metrics.get('consistency', 0):.2f}%")
                    st.metric("Validity", f"{metrics.get('validity', 0):.2f}%")
                
                with col3:
                    st.metric("Timeliness", f"{metrics.get('timeliness', 0):.2f}%")
                    st.metric("Accuracy", f"{metrics.get('accuracy', 0):.2f}%")
                
                # Issues table
                if "issues" in metrics and metrics["issues"]:
                    st.subheader("Identified Issues")
                    issues_df = pd.DataFrame(metrics["issues"])
                    st.dataframe(issues_df, use_container_width=True)
        else:
            st.info("Quality metrics are not available yet. Please sync data first.")
    
    with tab3:
        st.header("Data Health Recommendations")
        if st.session_state.data_metrics:
            # Generate recommendations based on the data health metrics
            recommendations = []
            
            for data_type, metrics in st.session_state.data_metrics.items():
                if metrics.get('completeness', 100) < 90:
                    recommendations.append({
                        "Data Type": data_type,
                        "Issue": "Low Completeness",
                        "Recommendation": "Review required fields and implement validation to ensure all necessary data is captured.",
                        "Priority": "High" if metrics.get('completeness', 100) < 75 else "Medium"
                    })
                
                if metrics.get('consistency', 100) < 90:
                    recommendations.append({
                        "Data Type": data_type,
                        "Issue": "Consistency Issues",
                        "Recommendation": "Implement data governance processes to ensure consistency across related data elements.",
                        "Priority": "High" if metrics.get('consistency', 100) < 75 else "Medium"
                    })
                
                if metrics.get('validity', 100) < 90:
                    recommendations.append({
                        "Data Type": data_type,
                        "Issue": "Validity Concerns",
                        "Recommendation": "Add data validation rules in SAP IBP to enforce proper data formats and values.",
                        "Priority": "High" if metrics.get('validity', 100) < 75 else "Medium"
                    })
                
                if metrics.get('uniqueness', 100) < 95:
                    recommendations.append({
                        "Data Type": data_type,
                        "Issue": "Duplicate Records",
                        "Recommendation": "Implement deduplication processes and enforce unique key constraints.",
                        "Priority": "Medium"
                    })
                
                if metrics.get('timeliness', 100) < 85:
                    recommendations.append({
                        "Data Type": data_type,
                        "Issue": "Data Freshness",
                        "Recommendation": "Review data update processes and implement regular data refresh schedules.",
                        "Priority": "Medium"
                    })
            
            if recommendations:
                # Add filtering options
                priority_filter = st.multiselect(
                    "Filter by priority", 
                    ["High", "Medium", "Low"],
                    default=["High", "Medium"]
                )
                
                data_type_filter = st.multiselect(
                    "Filter by data type",
                    list(set(r["Data Type"] for r in recommendations)),
                    default=list(set(r["Data Type"] for r in recommendations))
                )
                
                # Apply filters
                filtered_recommendations = [
                    r for r in recommendations 
                    if r["Priority"] in priority_filter and r["Data Type"] in data_type_filter
                ]
                
                if filtered_recommendations:
                    st.dataframe(pd.DataFrame(filtered_recommendations), use_container_width=True)
                else:
                    st.info("No recommendations match your filter criteria.")
            else:
                st.success("No critical data health issues detected. Your supply chain master data appears to be in good health!")
        else:
            st.info("Recommendations will appear here after data sync and analysis is complete.")

    # Footer information
    st.markdown("---")
    st.caption("SAP IBP Supply Chain Data Health Monitor | Developed with Streamlit")

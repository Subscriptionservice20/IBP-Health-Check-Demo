# SAP IBP Supply Chain Data Health Monitor

A Streamlit application for monitoring and analyzing supply chain master data quality in SAP Integrated Business Planning (IBP) systems.

## Features

- **Master Data Quality Assessment**: Evaluate completeness, accuracy, and consistency of your supply chain master data
- **Data Health Dashboards**: Visualize key metrics with interactive charts
- **Time-Series Analysis**: Track data quality improvements over time
- **Customizable Reports**: Generate detailed reports on specific data domains
- **Issue Identification**: Automatically detect common data problems affecting supply chain planning
- **Demo Mode**: Explore the application features with simulated data

## Getting Started

1. Clone this repository
2. Install the required packages with `pip install -r requirements.txt`
3. Run the application with `streamlit run app.py`
4. Use Demo Mode to explore the application, or connect to your SAP IBP instance

## Demo Mode

The application includes a Demo Mode that generates realistic supply chain master data with intentional quality issues for demonstration purposes. This allows you to explore all the application features without needing an actual SAP IBP connection.

## Requirements

- Python 3.11+
- Streamlit
- Pandas
- Plotly
- NumPy
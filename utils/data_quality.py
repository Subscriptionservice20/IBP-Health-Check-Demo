import pandas as pd
import numpy as np
import datetime
from typing import Dict, List, Optional, Any, Tuple

class DataQualityAnalyzer:
    """
    Analyzer for supply chain master data quality metrics.
    Calculates various data health indicators and identifies issues.
    """
    
    def __init__(self, master_data: Dict[str, pd.DataFrame]):
        """
        Initialize the data quality analyzer.
        
        Args:
            master_data: Dictionary containing master data DataFrames by type
        """
        self.master_data = master_data
        self.quality_dimensions = [
            "completeness", 
            "consistency", 
            "validity", 
            "uniqueness", 
            "timeliness", 
            "accuracy"
        ]
    
    def calculate_quality_scores(self) -> Dict[str, float]:
        """
        Calculate overall quality scores for each data type.
        
        Returns:
            Dict[str, float]: Dictionary with data types as keys and quality scores (0-10) as values
        """
        quality_scores = {}
        
        for data_type, data in self.master_data.items():
            if isinstance(data, pd.DataFrame) and not data.empty:
                # Calculate individual metrics
                metrics = self.analyze_data_health_for_type(data_type, data)
                
                # Calculate weighted average score (0-10 scale)
                weights = {
                    "completeness": 0.25,
                    "consistency": 0.2,
                    "validity": 0.2,
                    "uniqueness": 0.15,
                    "timeliness": 0.1,
                    "accuracy": 0.1
                }
                
                weighted_score = 0
                for dimension, weight in weights.items():
                    if dimension in metrics:
                        # Convert percentage to 0-10 scale
                        score = metrics[dimension] / 10
                        weighted_score += score * weight
                
                quality_scores[data_type] = min(weighted_score, 10)  # Cap at 10
            else:
                quality_scores[data_type] = 0
        
        return quality_scores
    
    def analyze_data_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze the health of all master data types.
        
        Returns:
            Dict: Dictionary with data types as keys and metrics dictionaries as values
        """
        results = {}
        
        for data_type, data in self.master_data.items():
            if isinstance(data, pd.DataFrame) and not data.empty:
                results[data_type] = self.analyze_data_health_for_type(data_type, data)
            else:
                results[data_type] = {dimension: 0 for dimension in self.quality_dimensions}
                results[data_type]["issues"] = [{"field": "all", "issue": "No data available", "impact": "High"}]
        
        return results
    
    def analyze_data_health_for_type(self, data_type: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the health metrics for a specific data type.
        
        Args:
            data_type: The type of master data
            data: DataFrame containing the master data
            
        Returns:
            Dict: Dictionary of metrics and issues
        """
        metrics = {}
        issues = []
        
        # 1. Completeness - percentage of non-null values
        metrics["completeness"] = self._calculate_completeness(data)
        if metrics["completeness"] < 95:
            # Identify fields with high null counts
            null_counts = data.isnull().sum()
            problem_fields = null_counts[null_counts > 0].sort_values(ascending=False)
            
            for field, count in problem_fields.items():
                null_percentage = (count / len(data)) * 100
                if null_percentage > 5:  # More than 5% missing
                    impact = "High" if null_percentage > 20 else "Medium"
                    issues.append({
                        "field": field,
                        "issue": f"Missing values ({null_percentage:.1f}%)",
                        "impact": impact
                    })
        
        # 2. Consistency - check for consistent formats and values
        metrics["consistency"] = self._calculate_consistency(data_type, data)
        
        # 3. Validity - check for valid values according to business rules
        metrics["validity"] = self._calculate_validity(data_type, data)
        
        # 4. Uniqueness - check for duplicates in key fields
        metrics["uniqueness"] = self._calculate_uniqueness(data_type, data)
        if metrics["uniqueness"] < 100:
            issues.append({
                "field": "Key fields",
                "issue": "Duplicate records detected",
                "impact": "High" if metrics["uniqueness"] < 90 else "Medium"
            })
        
        # 5. Timeliness - check for recently updated records
        metrics["timeliness"] = self._calculate_timeliness(data)
        if metrics["timeliness"] < 80:
            issues.append({
                "field": "Last updated",
                "issue": "Many records not recently updated",
                "impact": "Medium"
            })
        
        # 6. Accuracy - estimated based on other metrics and specific checks
        metrics["accuracy"] = self._calculate_accuracy(data_type, data)
        
        # Add issues to the metrics
        metrics["issues"] = issues
        
        return metrics
    
    def _calculate_completeness(self, data: pd.DataFrame) -> float:
        """
        Calculate the completeness percentage of the data.
        
        Args:
            data: DataFrame to analyze
            
        Returns:
            float: Completeness percentage (0-100)
        """
        if data.empty:
            return 0
            
        total_cells = data.size
        missing_cells = data.isnull().sum().sum()
        
        if total_cells == 0:
            return 0
            
        completeness = 100 * (1 - (missing_cells / total_cells))
        return completeness
    
    def _calculate_consistency(self, data_type: str, data: pd.DataFrame) -> float:
        """
        Calculate consistency score based on format consistency and expected patterns.
        
        Args:
            data_type: Type of master data
            data: DataFrame to analyze
            
        Returns:
            float: Consistency percentage (0-100)
        """
        if data.empty:
            return 0
            
        consistency_scores = []
        
        # Generic consistency checks
        # 1. Check for mixed data types in columns
        for col in data.columns:
            # Skip columns that are all null
            if data[col].isnull().all():
                continue
                
            # If column should be numeric, check for non-numeric values
            if data[col].dtype in [np.int64, np.float64]:
                non_numeric = data[col].apply(lambda x: pd.notna(x) and not isinstance(x, (int, float)))
                if non_numeric.any():
                    consistency_scores.append(100 * (1 - non_numeric.mean()))
            
            # If column is string type, check for inconsistent case if relevant
            if data[col].dtype == object:
                # Sample non-null values to check case consistency
                non_null_values = data[col].dropna()
                if len(non_null_values) > 0:
                    # Check if case appears inconsistent (mix of upper, lower, title case)
                    upper_case = non_null_values.str.isupper().mean() if hasattr(non_null_values.str, 'isupper') else 0
                    lower_case = non_null_values.str.islower().mean() if hasattr(non_null_values.str, 'islower') else 0
                    title_case = non_null_values.str.istitle().mean() if hasattr(non_null_values.str, 'istitle') else 0
                    
                    # If there's a clear dominant case format, score based on consistency to that format
                    max_case = max(upper_case, lower_case, title_case)
                    if max_case > 0.5:  # There's a dominant case format
                        consistency_scores.append(100 * max_case)
        
        # Specific consistency checks by data type
        if data_type == "Products":
            # Check product code format consistency if exists
            if "ProductID" in data.columns:
                # Assume product codes should follow consistent pattern (length, prefix, etc.)
                product_codes = data["ProductID"].dropna().astype(str)
                if len(product_codes) > 0:
                    # Check length consistency
                    length_consistency = 100 * (1 - product_codes.str.len().std() / product_codes.str.len().mean())
                    if not np.isnan(length_consistency):
                        consistency_scores.append(max(0, min(100, length_consistency)))
        
        elif data_type == "Locations":
            # Check location code format consistency
            if "LocationID" in data.columns:
                location_codes = data["LocationID"].dropna().astype(str)
                if len(location_codes) > 0:
                    # Check for consistent format (e.g., all uppercase or all following same pattern)
                    code_pattern_consistency = 100 * (1 - (location_codes.str.len().std() / location_codes.str.len().mean()))
                    if not np.isnan(code_pattern_consistency):
                        consistency_scores.append(max(0, min(100, code_pattern_consistency)))
        
        # If no specific checks were applicable, use a default high score
        if not consistency_scores:
            return 95.0
        
        # Return average consistency score
        return sum(consistency_scores) / len(consistency_scores)
    
    def _calculate_validity(self, data_type: str, data: pd.DataFrame) -> float:
        """
        Calculate validity score based on business rules and expected values.
        
        Args:
            data_type: Type of master data
            data: DataFrame to analyze
            
        Returns:
            float: Validity percentage (0-100)
        """
        if data.empty:
            return 0
            
        validity_scores = []
        
        # Generic validity checks
        # Check date fields are in valid ranges
        date_columns = [col for col in data.columns if "date" in col.lower() or "time" in col.lower()]
        for col in date_columns:
            if data[col].dtype == 'datetime64[ns]' or pd.api.types.is_datetime64_any_dtype(data[col]):
                # Check for future dates where not expected
                if "future" not in col.lower() and "forecast" not in col.lower():
                    future_dates = data[col] > datetime.datetime.now()
                    invalid_future = future_dates.mean() if not future_dates.empty else 0
                    validity_scores.append(100 * (1 - invalid_future))
        
        # Specific validity checks by data type
        if data_type == "Products":
            # Check for valid product categories
            if "ProductCategory" in data.columns:
                # Check if values are in expected set
                valid_categories = ["RAW", "WIP", "FG", "SPARE", "SERVICE"]
                if data["ProductCategory"].dtype == object:  # String column
                    valid_percent = 100 * (data["ProductCategory"].isin(valid_categories) | data["ProductCategory"].isna()).mean()
                    validity_scores.append(valid_percent)
            
            # Check for valid UoM codes
            if "UnitOfMeasure" in data.columns:
                valid_uoms = ["EA", "KG", "L", "M", "PC", "CS"]
                if data["UnitOfMeasure"].dtype == object:  # String column
                    valid_percent = 100 * (data["UnitOfMeasure"].isin(valid_uoms) | data["UnitOfMeasure"].isna()).mean()
                    validity_scores.append(valid_percent)
        
        elif data_type == "Locations":
            # Check for valid location types
            if "LocationType" in data.columns:
                valid_types = ["PLANT", "DC", "WAREHOUSE", "STORE", "SUPPLIER", "CUSTOMER"]
                if data["LocationType"].dtype == object:  # String column
                    valid_percent = 100 * (data["LocationType"].isin(valid_types) | data["LocationType"].isna()).mean()
                    validity_scores.append(valid_percent)
        
        # If no specific checks were applicable, use a default good score
        if not validity_scores:
            return 90.0
        
        # Return average validity score
        return sum(validity_scores) / len(validity_scores)
    
    def _calculate_uniqueness(self, data_type: str, data: pd.DataFrame) -> float:
        """
        Calculate uniqueness score based on duplicate key checks.
        
        Args:
            data_type: Type of master data
            data: DataFrame to analyze
            
        Returns:
            float: Uniqueness percentage (0-100)
        """
        if data.empty:
            return 0
            
        # Determine key fields based on data type
        key_fields = self._get_key_fields(data_type, data)
        
        if not key_fields:
            # If no key fields identified, assume good uniqueness
            return 98.0
        
        # Check for duplicates in key fields
        if all(field in data.columns for field in key_fields):
            # Count unique combinations of key fields
            total_records = len(data)
            unique_records = len(data[key_fields].drop_duplicates())
            
            if total_records == 0:
                return 0
                
            uniqueness = 100 * (unique_records / total_records)
            return uniqueness
        else:
            # If key fields don't exist, return a neutral score
            return 90.0
    
    def _calculate_timeliness(self, data: pd.DataFrame) -> float:
        """
        Calculate timeliness score based on last update timestamps.
        
        Args:
            data: DataFrame to analyze
            
        Returns:
            float: Timeliness percentage (0-100)
        """
        if data.empty:
            return 0
            
        # Look for update timestamp columns
        timestamp_columns = [col for col in data.columns if
                             any(term in col.lower() for term in ["update", "modified", "change", "timestamp"])]
        
        if not timestamp_columns:
            # No timestamp columns found, assume neutral timeliness
            return 85.0
        
        # Use the most recent timestamp column
        timestamp_col = timestamp_columns[0]
        
        if data[timestamp_col].dtype != 'datetime64[ns]' and not pd.api.types.is_datetime64_any_dtype(data[timestamp_col]):
            # Not a valid timestamp column
            return 85.0
        
        # Calculate how many records were updated recently (last 90 days)
        now = datetime.datetime.now()
        threshold_date = now - datetime.timedelta(days=90)
        
        recent_updates = (data[timestamp_col] >= threshold_date).mean()
        
        # Convert to percentage
        timeliness = 100 * recent_updates
        
        return timeliness
    
    def _calculate_accuracy(self, data_type: str, data: pd.DataFrame) -> float:
        """
        Estimate accuracy score based on specific checks and other metrics.
        
        Args:
            data_type: Type of master data
            data: DataFrame to analyze
            
        Returns:
            float: Accuracy percentage (0-100)
        """
        if data.empty:
            return 0
            
        accuracy_scores = []
        
        # Specific accuracy checks by data type
        if data_type == "Products":
            # Check for reasonable product weights/dimensions
            numeric_columns = ["Weight", "Length", "Width", "Height", "Volume"]
            
            for col in numeric_columns:
                if col in data.columns and pd.api.types.is_numeric_dtype(data[col]):
                    # Check for negative values (should not exist)
                    negative_values = (data[col] < 0).mean()
                    accuracy_scores.append(100 * (1 - negative_values))
                    
                    # Check for extreme outliers that might indicate errors
                    non_null_values = data[col].dropna()
                    if len(non_null_values) > 0:
                        q1 = non_null_values.quantile(0.25)
                        q3 = non_null_values.quantile(0.75)
                        iqr = q3 - q1
                        
                        # Define extreme outliers (more than 5 IQRs from Q1 or Q3)
                        lower_bound = q1 - (5 * iqr)
                        upper_bound = q3 + (5 * iqr)
                        
                        extreme_outliers = ((non_null_values < lower_bound) | (non_null_values > upper_bound)).mean()
                        accuracy_scores.append(100 * (1 - extreme_outliers))
        
        elif data_type == "Locations":
            # Check for valid coordinates if present
            coordinate_columns = ["Latitude", "Longitude"]
            
            if all(col in data.columns for col in coordinate_columns):
                # Check latitude range (-90 to 90)
                if pd.api.types.is_numeric_dtype(data["Latitude"]):
                    invalid_lat = ((data["Latitude"] < -90) | (data["Latitude"] > 90)).mean()
                    accuracy_scores.append(100 * (1 - invalid_lat))
                
                # Check longitude range (-180 to 180)
                if pd.api.types.is_numeric_dtype(data["Longitude"]):
                    invalid_lon = ((data["Longitude"] < -180) | (data["Longitude"] > 180)).mean()
                    accuracy_scores.append(100 * (1 - invalid_lon))
        
        # If no specific checks were applicable, derive score from other metrics
        if not accuracy_scores:
            # Estimate accuracy based on completeness, consistency and validity
            completeness = self._calculate_completeness(data)
            consistency = self._calculate_consistency(data_type, data)
            validity = self._calculate_validity(data_type, data)
            
            # Weighted average
            estimated_accuracy = (0.4 * completeness + 0.3 * consistency + 0.3 * validity)
            
            # Cap at 95% since we can't fully verify accuracy without ground truth
            return min(95.0, estimated_accuracy)
        
        # Return average accuracy score
        return sum(accuracy_scores) / len(accuracy_scores)
    
    def _get_key_fields(self, data_type: str, data: pd.DataFrame) -> List[str]:
        """
        Identify the key fields for a specific data type.
        
        Args:
            data_type: Type of master data
            data: DataFrame containing the data
            
        Returns:
            List[str]: List of column names that serve as key fields
        """
        # Define key fields by data type
        key_mapping = {
            "Products": ["ProductID"],
            "Locations": ["LocationID"],
            "Customers": ["CustomerID"],
            "Suppliers": ["SupplierID"],
            "Time Profiles": ["TimeProfileID"],
            "Resource Plans": ["ResourceID"]
        }
        
        # Return the mapped key fields if they exist in the DataFrame
        if data_type in key_mapping:
            keys = key_mapping[data_type]
            # Filter to only include keys that exist in the DataFrame
            return [key for key in keys if key in data.columns]
        
        # If no mapping exists, try to identify ID columns
        id_columns = [col for col in data.columns if "id" in col.lower() or "code" in col.lower() or "key" in col.lower()]
        return id_columns[:1] if id_columns else []  # Return first ID column if any

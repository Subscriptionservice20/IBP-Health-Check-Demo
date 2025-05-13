import requests
import pandas as pd
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union

class SAPConnector:
    """
    A connector class for SAP IBP (Integrated Business Planning) that handles
    API authentication and data retrieval for supply chain master data.
    """
    
    def __init__(self, url: str, client: str, username: str, password: str):
        """
        Initialize the SAP IBP connector.
        
        Args:
            url: The base URL for the SAP IBP instance
            client: The SAP client ID
            username: The SAP username
            password: The SAP password
        """
        self.url = url
        self.client = client
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = None
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """
        Test the connection to SAP IBP.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Attempt to get a token as a connection test
            token = self._get_auth_token()
            return token is not None
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def _get_auth_token(self) -> Optional[str]:
        """
        Get an authentication token from SAP IBP.
        
        Returns:
            str: The authentication token or None if authentication fails
        """
        # Check if we have a valid token already
        if self.token and self.token_expiry and time.time() < self.token_expiry:
            return self.token
        
        try:
            # Construct the auth endpoint
            auth_url = f"{self.url}/sap/opu/odata/sap/IBPAUTHENTICATION;v=0002"
            
            # Set up headers for token request
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-csrf-token": "fetch"
            }
            
            # Make a GET request to fetch CSRF token
            response = requests.get(
                auth_url,
                headers=headers,
                auth=(f"{self.username}@{self.client}", self.password),
                timeout=30
            )
            
            if response.status_code == 200:
                # Extract CSRF token from headers
                csrf_token = response.headers.get("x-csrf-token")
                
                if csrf_token:
                    # Set token expiry (typical SAP tokens last 24 hours, using 23 to be safe)
                    self.token = csrf_token
                    self.token_expiry = time.time() + (23 * 60 * 60)
                    return csrf_token
                else:
                    self.logger.error("No CSRF token found in response headers")
            else:
                self.logger.error(f"Authentication failed with status code: {response.status_code}")
                self.logger.error(f"Response text: {response.text}")
            
            return None
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return None
    
    def fetch_master_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        Fetch master data from SAP IBP based on data type.
        
        Args:
            data_type: Type of master data to fetch (products, locations, customers, etc.)
            
        Returns:
            pd.DataFrame: DataFrame containing the requested master data or None if the request fails
        """
        # Get authentication token
        token = self._get_auth_token()
        if not token:
            self.logger.error("Failed to get authentication token")
            return None
        
        try:
            # Determine the endpoint based on data type
            endpoint = self._get_endpoint_for_data_type(data_type)
            
            if not endpoint:
                self.logger.error(f"No endpoint found for data type: {data_type}")
                return None
            
            # Set up request headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-csrf-token": token
            }
            
            # Make the API request
            response = requests.get(
                f"{self.url}{endpoint}",
                headers=headers,
                auth=(f"{self.username}@{self.client}", self.password),
                timeout=60
            )
            
            if response.status_code == 200:
                # Parse the response
                data = response.json()
                
                # Process the data into a DataFrame
                return self._process_response_to_dataframe(data, data_type)
            else:
                self.logger.error(f"Data fetch failed with status code: {response.status_code}")
                self.logger.error(f"Response text: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error fetching {data_type} data: {str(e)}")
            return None
    
    def _get_endpoint_for_data_type(self, data_type: str) -> Optional[str]:
        """
        Map data type to the appropriate SAP IBP API endpoint.
        
        Args:
            data_type: Type of master data
            
        Returns:
            str: The API endpoint or None if the data type is not supported
        """
        # Define endpoints for different data types
        endpoints = {
            "products": "/sap/opu/odata/IBP/PRODUCT_MASTER_SRV/Products",
            "locations": "/sap/opu/odata/IBP/LOCATION_MASTER_SRV/Locations",
            "customers": "/sap/opu/odata/IBP/CUSTOMER_MASTER_SRV/Customers",
            "suppliers": "/sap/opu/odata/IBP/SUPPLIER_MASTER_SRV/Suppliers",
            "time_profiles": "/sap/opu/odata/IBP/TIMEPROFILE_MASTER_SRV/TimeProfiles",
            "resource_plans": "/sap/opu/odata/IBP/RESOURCE_MASTER_SRV/Resources"
        }
        
        return endpoints.get(data_type)
    
    def _process_response_to_dataframe(self, response_data: Dict[str, Any], data_type: str) -> pd.DataFrame:
        """
        Process the API response into a pandas DataFrame.
        
        Args:
            response_data: The JSON response from SAP IBP
            data_type: The type of data being processed
            
        Returns:
            pd.DataFrame: The processed data as a DataFrame
        """
        try:
            # SAP OData responses typically have a 'd' property containing the results
            if 'd' in response_data:
                # Results might be in 'results' array or directly in 'd'
                if 'results' in response_data['d']:
                    data_list = response_data['d']['results']
                else:
                    data_list = [response_data['d']]
            else:
                data_list = response_data.get('value', [])
            
            # Convert to DataFrame
            if data_list:
                df = pd.DataFrame(data_list)
                
                # Clean up the DataFrame
                # Remove metadata and navigation properties
                columns_to_drop = [col for col in df.columns if col.startswith('__') or col.endswith('@odata')]
                if columns_to_drop:
                    df = df.drop(columns=columns_to_drop)
                
                return df
            else:
                self.logger.warning(f"No data found for {data_type}")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error processing {data_type} data: {str(e)}")
            return pd.DataFrame()
    
    def submit_data_correction(self, data_type: str, record_id: str, corrections: Dict[str, Any]) -> bool:
        """
        Submit corrections to SAP IBP for a specific data record.
        
        Args:
            data_type: Type of master data
            record_id: ID of the record to correct
            corrections: Dictionary of field-value pairs to update
            
        Returns:
            bool: True if correction was submitted successfully, False otherwise
        """
        # Get authentication token
        token = self._get_auth_token()
        if not token:
            self.logger.error("Failed to get authentication token")
            return False
        
        try:
            # Determine the endpoint
            base_endpoint = self._get_endpoint_for_data_type(data_type)
            if not base_endpoint:
                self.logger.error(f"No endpoint found for data type: {data_type}")
                return False
            
            # Construct the specific record endpoint
            record_endpoint = f"{base_endpoint}('{record_id}')"
            
            # Set up request headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-csrf-token": token
            }
            
            # Make the PATCH request to update the record
            response = requests.patch(
                f"{self.url}{record_endpoint}",
                headers=headers,
                auth=(f"{self.username}@{self.client}", self.password),
                json=corrections,
                timeout=30
            )
            
            if response.status_code in [200, 201, 204]:
                self.logger.info(f"Successfully updated {data_type} record {record_id}")
                return True
            else:
                self.logger.error(f"Data correction failed with status code: {response.status_code}")
                self.logger.error(f"Response text: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error submitting correction for {data_type} record {record_id}: {str(e)}")
            return False

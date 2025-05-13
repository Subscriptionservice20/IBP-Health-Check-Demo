import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any

def generate_demo_data() -> Dict[str, pd.DataFrame]:
    """
    Generate realistic demo data for supply chain master data elements.
    
    Returns:
        Dict[str, pd.DataFrame]: Dictionary with data types as keys and DataFrames as values
    """
    # Set seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Generate demo data for each master data type
    master_data = {
        "Products": generate_product_data(),
        "Locations": generate_location_data(),
        "Customers": generate_customer_data(),
        "Suppliers": generate_supplier_data(),
        "Time Profiles": generate_time_profile_data(),
        "Resource Plans": generate_resource_plan_data()
    }
    
    return master_data

def generate_product_data(num_records: int = 200) -> pd.DataFrame:
    """Generate realistic product master data."""
    # Product categories and subcategories
    categories = ["RAW", "WIP", "FG", "SPARE", "SERVICE"]
    subcategories = ["ELECTRONICS", "MECHANICAL", "CHEMICAL", "PACKAGING", "CONSUMABLE"]
    uoms = ["EA", "KG", "L", "M", "PC", "CS"]
    
    # Create product IDs with realistic patterns
    product_ids = [f"P{str(i).zfill(6)}" for i in range(1, num_records + 1)]
    
    # Generate data with some realistic patterns and issues
    data = {
        "ProductID": product_ids,
        "ProductName": [f"Product {i}" for i in range(1, num_records + 1)],
        "ProductCategory": np.random.choice(categories, num_records, p=[0.2, 0.3, 0.3, 0.1, 0.1]),
        "ProductSubcategory": np.random.choice(subcategories, num_records),
        "UnitOfMeasure": np.random.choice(uoms, num_records, p=[0.5, 0.2, 0.1, 0.1, 0.05, 0.05]),
        "GrossWeight": np.random.uniform(0.1, 100, num_records).round(2),
        "NetWeight": np.random.uniform(0.1, 90, num_records).round(2),
        "ShelfLife": np.random.choice([30, 60, 90, 180, 365, np.nan], num_records),
        "Price": np.random.uniform(1, 1000, num_records).round(2),
        "Active": np.random.choice([True, False], num_records, p=[0.9, 0.1]),
        "CreatedOn": [datetime.now() - timedelta(days=random.randint(30, 365)) for _ in range(num_records)],
        "LastUpdated": [datetime.now() - timedelta(days=random.randint(0, 30)) for _ in range(num_records)]
    }
    
    # Introduce some data quality issues
    df = pd.DataFrame(data)
    
    # 1. Missing values in some fields (5-15% missing)
    for field in ["ProductSubcategory", "GrossWeight", "ShelfLife", "Price"]:
        mask = np.random.choice([True, False], len(df), p=[0.1, 0.9])
        df.loc[mask, field] = np.nan
    
    # 2. Inconsistent format in some product names
    mask = np.random.choice([True, False], len(df), p=[0.05, 0.95])
    df.loc[mask, "ProductName"] = df.loc[mask, "ProductName"].str.upper()
    
    # 3. Invalid values in some fields
    mask = np.random.choice([True, False], len(df), p=[0.03, 0.97])
    df.loc[mask, "UnitOfMeasure"] = "INVALID"
    
    # 4. Ensure some data integrity issues (net weight > gross weight for some products)
    mask = np.random.choice([True, False], len(df), p=[0.05, 0.95])
    df.loc[mask, "NetWeight"] = df.loc[mask, "GrossWeight"] + np.random.uniform(1, 10, mask.sum()).round(2)
    
    # 5. Some products with no updates recently
    mask = np.random.choice([True, False], len(df), p=[0.2, 0.8])
    df.loc[mask, "LastUpdated"] = df.loc[mask, "CreatedOn"]
    
    return df

def generate_location_data(num_records: int = 100) -> pd.DataFrame:
    """Generate realistic location master data."""
    location_types = ["PLANT", "DC", "WAREHOUSE", "STORE", "SUPPLIER", "CUSTOMER"]
    countries = ["US", "CA", "MX", "DE", "FR", "UK", "CN", "JP", "IN", "BR"]
    regions = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]
    
    # Create location IDs with realistic patterns
    location_ids = [f"L{str(i).zfill(4)}" for i in range(1, num_records + 1)]
    
    # Generate data
    data = {
        "LocationID": location_ids,
        "LocationName": [f"Location {i}" for i in range(1, num_records + 1)],
        "LocationType": np.random.choice(location_types, num_records),
        "Address": [f"{random.randint(100, 9999)} Main St" for _ in range(num_records)],
        "City": [f"City {i % 30}" for i in range(num_records)],
        "Country": np.random.choice(countries, num_records),
        "Region": np.random.choice(regions, num_records),
        "Capacity": np.random.uniform(1000, 100000, num_records).round(0),
        "ParentLocation": [f"L{str(random.randint(1, 20)).zfill(4)}" if random.random() > 0.3 else None for _ in range(num_records)],
        "Active": np.random.choice([True, False], num_records, p=[0.95, 0.05]),
        "CreatedOn": [datetime.now() - timedelta(days=random.randint(100, 730)) for _ in range(num_records)],
        "LastUpdated": [datetime.now() - timedelta(days=random.randint(0, 90)) for _ in range(num_records)]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Introduce some data quality issues
    
    # 1. Missing values in some fields
    for field in ["Address", "Region", "Capacity", "ParentLocation"]:
        mask = np.random.choice([True, False], len(df), p=[0.15, 0.85])
        df.loc[mask, field] = np.nan
    
    # 2. Inconsistent format in location names
    mask = np.random.choice([True, False], len(df), p=[0.07, 0.93])
    df.loc[mask, "LocationName"] = df.loc[mask, "LocationName"].str.lower()
    
    # 3. Some invalid location references
    mask = np.random.choice([True, False], len(df), p=[0.05, 0.95])
    df.loc[mask, "ParentLocation"] = "INVALID_LOC"
    
    # 4. Some locations with no updates recently
    mask = np.random.choice([True, False], len(df), p=[0.25, 0.75])
    df.loc[mask, "LastUpdated"] = df.loc[mask, "CreatedOn"]
    
    return df

def generate_customer_data(num_records: int = 150) -> pd.DataFrame:
    """Generate realistic customer master data."""
    customer_types = ["RETAIL", "WHOLESALE", "DISTRIBUTOR", "DIRECT", "ONLINE"]
    payment_terms = ["NET30", "NET60", "NET90", "PREPAID"]
    
    # Create customer IDs
    customer_ids = [f"C{str(i).zfill(5)}" for i in range(1, num_records + 1)]
    
    # Generate data
    data = {
        "CustomerID": customer_ids,
        "CustomerName": [f"Customer {i}" for i in range(1, num_records + 1)],
        "CustomerType": np.random.choice(customer_types, num_records),
        "ContactPerson": [f"Contact {i % 50}" for i in range(num_records)],
        "Email": [f"contact{i}@customer{i % 100}.com" for i in range(num_records)],
        "Phone": [f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}" for _ in range(num_records)],
        "PaymentTerms": np.random.choice(payment_terms, num_records),
        "CreditLimit": np.random.uniform(10000, 1000000, num_records).round(-3),
        "PrimaryLocationID": [f"L{str(random.randint(1, 100)).zfill(4)}" for _ in range(num_records)],
        "Active": np.random.choice([True, False], num_records, p=[0.9, 0.1]),
        "CreatedOn": [datetime.now() - timedelta(days=random.randint(30, 730)) for _ in range(num_records)],
        "LastUpdated": [datetime.now() - timedelta(days=random.randint(0, 60)) for _ in range(num_records)]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Introduce some data quality issues
    
    # 1. Missing values in some fields
    for field in ["ContactPerson", "Email", "Phone", "CreditLimit"]:
        mask = np.random.choice([True, False], len(df), p=[0.12, 0.88])
        df.loc[mask, field] = np.nan
    
    # 2. Invalid email formats for some records
    mask = np.random.choice([True, False], len(df), p=[0.08, 0.92])
    df.loc[mask, "Email"] = df.loc[mask, "Email"].str.replace("@", "#")
    
    # 3. Some customers with missing location reference
    mask = np.random.choice([True, False], len(df), p=[0.1, 0.9])
    df.loc[mask, "PrimaryLocationID"] = np.nan
    
    # 4. Inconsistent phone formats
    mask = np.random.choice([True, False], len(df), p=[0.15, 0.85])
    df.loc[mask, "Phone"] = df.loc[mask, "Phone"].str.replace("+1-", "").str.replace("-", "")
    
    return df

def generate_supplier_data(num_records: int = 120) -> pd.DataFrame:
    """Generate realistic supplier master data."""
    supplier_types = ["MANUFACTURER", "DISTRIBUTOR", "SERVICE", "RAW_MATERIAL", "PACKAGING"]
    payment_terms = ["NET30", "NET45", "NET60", "IMMEDIATE"]
    
    # Create supplier IDs
    supplier_ids = [f"S{str(i).zfill(5)}" for i in range(1, num_records + 1)]
    
    # Generate data
    data = {
        "SupplierID": supplier_ids,
        "SupplierName": [f"Supplier {i}" for i in range(1, num_records + 1)],
        "SupplierType": np.random.choice(supplier_types, num_records),
        "ContactPerson": [f"Contact {i % 40}" for i in range(num_records)],
        "Email": [f"contact{i}@supplier{i % 80}.com" for i in range(num_records)],
        "Phone": [f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}" for _ in range(num_records)],
        "PaymentTerms": np.random.choice(payment_terms, num_records),
        "LeadTime": np.random.choice([7, 14, 21, 30, 45, 60, 90], num_records),
        "QualityRating": np.random.uniform(1, 5, num_records).round(1),
        "PrimaryLocationID": [f"L{str(random.randint(1, 100)).zfill(4)}" for _ in range(num_records)],
        "Active": np.random.choice([True, False], num_records, p=[0.93, 0.07]),
        "CreatedOn": [datetime.now() - timedelta(days=random.randint(30, 730)) for _ in range(num_records)],
        "LastUpdated": [datetime.now() - timedelta(days=random.randint(0, 60)) for _ in range(num_records)]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Introduce some data quality issues
    
    # 1. Missing values in some fields
    for field in ["ContactPerson", "Email", "LeadTime", "QualityRating"]:
        mask = np.random.choice([True, False], len(df), p=[0.1, 0.9])
        df.loc[mask, field] = np.nan
    
    # 2. Some invalid lead times (negative values)
    mask = np.random.choice([True, False], len(df), p=[0.03, 0.97])
    df.loc[mask, "LeadTime"] = df.loc[mask, "LeadTime"] * -1
    
    # 3. Quality ratings out of expected range
    mask = np.random.choice([True, False], len(df), p=[0.05, 0.95])
    df.loc[mask, "QualityRating"] = np.random.uniform(5.1, 10, mask.sum()).round(1)
    
    # 4. Some suppliers with missing location reference
    mask = np.random.choice([True, False], len(df), p=[0.08, 0.92])
    df.loc[mask, "PrimaryLocationID"] = np.nan
    
    return df

def generate_time_profile_data(num_records: int = 30) -> pd.DataFrame:
    """Generate realistic time profile master data."""
    time_units = ["DAY", "WEEK", "MONTH", "QUARTER", "YEAR"]
    
    # Create time profile IDs
    profile_ids = [f"TP{str(i).zfill(3)}" for i in range(1, num_records + 1)]
    
    # Generate data
    data = {
        "ProfileID": profile_ids,
        "ProfileName": [f"Time Profile {i}" for i in range(1, num_records + 1)],
        "TimeUnit": np.random.choice(time_units, num_records),
        "PeriodLength": np.random.choice([1, 2, 3, 4, 6, 12], num_records),
        "StartDate": [datetime.now() - timedelta(days=random.randint(365, 730)) for _ in range(num_records)],
        "EndDate": [datetime.now() + timedelta(days=random.randint(365, 1095)) for _ in range(num_records)],
        "Description": [f"Planning profile for {unit.lower()} level planning" for unit in np.random.choice(time_units, num_records)],
        "Active": np.random.choice([True, False], num_records, p=[0.9, 0.1]),
        "CreatedOn": [datetime.now() - timedelta(days=random.randint(100, 500)) for _ in range(num_records)],
        "LastUpdated": [datetime.now() - timedelta(days=random.randint(0, 100)) for _ in range(num_records)]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Introduce some data quality issues
    
    # 1. Some end dates before start dates
    mask = np.random.choice([True, False], len(df), p=[0.1, 0.9])
    for idx in df[mask].index:
        df.at[idx, "EndDate"] = df.at[idx, "StartDate"] - timedelta(days=random.randint(1, 100))
    
    # 2. Missing descriptions
    mask = np.random.choice([True, False], len(df), p=[0.2, 0.8])
    df.loc[mask, "Description"] = np.nan
    
    # 3. Invalid period lengths for certain time units
    mask = (df["TimeUnit"] == "DAY") & (df["PeriodLength"] > 1)
    df.loc[mask, "PeriodLength"] = 1
    
    return df

def generate_resource_plan_data(num_records: int = 80) -> pd.DataFrame:
    """Generate realistic resource plan master data."""
    resource_types = ["MACHINE", "LABOR", "FACILITY", "TOOL", "VEHICLE"]
    capacity_units = ["HOURS", "UNITS", "BATCHES", "PALLETS", "SHIFTS"]
    
    # Create resource IDs
    resource_ids = [f"R{str(i).zfill(4)}" for i in range(1, num_records + 1)]
    
    # Generate data
    data = {
        "ResourceID": resource_ids,
        "ResourceName": [f"Resource {i}" for i in range(1, num_records + 1)],
        "ResourceType": np.random.choice(resource_types, num_records),
        "CapacityUnit": np.random.choice(capacity_units, num_records),
        "StandardCapacity": np.random.uniform(100, 10000, num_records).round(0),
        "LocationID": [f"L{str(random.randint(1, 100)).zfill(4)}" for _ in range(num_records)],
        "CostPerHour": np.random.uniform(10, 500, num_records).round(2),
        "EfficiencyRating": np.random.uniform(60, 100, num_records).round(1),
        "MaintenanceSchedule": [random.choice(["WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY", ""]) for _ in range(num_records)],
        "Active": np.random.choice([True, False], num_records, p=[0.9, 0.1]),
        "CreatedOn": [datetime.now() - timedelta(days=random.randint(30, 730)) for _ in range(num_records)],
        "LastUpdated": [datetime.now() - timedelta(days=random.randint(0, 60)) for _ in range(num_records)]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Introduce some data quality issues
    
    # 1. Missing values in some fields
    for field in ["StandardCapacity", "CostPerHour", "EfficiencyRating"]:
        mask = np.random.choice([True, False], len(df), p=[0.15, 0.85])
        df.loc[mask, field] = np.nan
    
    # 2. Some resources with efficiency rating outside expected range
    mask = np.random.choice([True, False], len(df), p=[0.07, 0.93])
    df.loc[mask, "EfficiencyRating"] = np.random.uniform(101, 150, mask.sum()).round(1)
    
    # 3. Some resources with missing location reference
    mask = np.random.choice([True, False], len(df), p=[0.1, 0.9])
    df.loc[mask, "LocationID"] = np.nan
    
    # 4. Inconsistent naming conventions
    mask = np.random.choice([True, False], len(df), p=[0.08, 0.92])
    df.loc[mask, "ResourceName"] = df.loc[mask, "ResourceName"].str.upper()
    
    return df
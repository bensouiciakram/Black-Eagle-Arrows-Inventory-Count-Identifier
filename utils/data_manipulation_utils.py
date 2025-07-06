"""
Data Manipulation Utilities for Black Eagle Arrows Inventory Scraper

This module provides data manipulation and processing functions for the Black Eagle Arrows
inventory scraper. It includes functions for data cleaning, standardization, and
transformation operations.

The module handles:
- Date formatting
- File name cleaning
- Data combination generation
- Column renaming
- Data standardization for reporting

Author: Project Developer
License: MIT
"""

from datetime import datetime 
from re import sub 
from itertools import product 
from typing import List, Dict, Any, Tuple, Optional
import logging

# Characters to clean from file names
name_cleaning_list = ['/', '"']

def format_date() -> str:
    """
    Format the current date as mm-dd-yyyy.
    
    Returns:
        str: Formatted date string
        
    Example:
        >>> format_date()
        '12-25-2023'
    """
    date = datetime.today()
    return f'{date.month}-{date.day}-{date.year}'

def clean_file_name(name: str) -> str:
    """
    Clean unwanted symbols from file name and add .html extension.
    
    This function removes invalid characters from file names and normalizes
    whitespace to create valid HTML file names.
    
    Args:
        name: Original file name to clean
        
    Returns:
        str: Cleaned file name with .html extension
        
    Example:
        >>> clean_file_name('Product Name/with "quotes"')
        'Product Name with quotes .html'
    """
    if not name:
        return 'unnamed_product.html'
    
    # Replace unwanted characters with spaces
    for element in name_cleaning_list:
        name = name.replace(element, ' ')
    
    # Normalize whitespace and add extension
    cleaned_name = sub(r'\s+', ' ', name).strip()
    return f"{cleaned_name}.html"

def get_all_combinations(*lists: List[str]) -> List[Tuple[str, ...]]:
    """
    Generate all possible combinations of values from multiple lists.
    
    This function uses itertools.product to generate all possible combinations
    of attribute values for product variations.
    
    Args:
        *lists: Variable number of lists containing attribute values
        
    Returns:
        List[Tuple[str, ...]]: All possible combinations as tuples
        
    Example:
        >>> get_all_combinations(['Red', 'Blue'], ['Small', 'Large'])
        [('Red', 'Small'), ('Red', 'Large'), ('Blue', 'Small'), ('Blue', 'Large')]
    """
    return list(product(*lists))

def rename_columns(data_container: List[Dict[str, Any]], **cols: str) -> List[Dict[str, Any]]:
    """
    Rename columns in a list of dictionaries.
    
    This function renames keys in dictionaries based on the provided mapping.
    If a key doesn't exist, it's set to an empty string.
    
    Args:
        data_container: List of dictionaries to process
        **cols: Column mapping (old_name=new_name)
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries with renamed keys
        
    Example:
        >>> data = [{'old_name': 'value'}]
        >>> rename_columns(data, old_name='new_name')
        [{'new_name': 'value'}]
    """
    result = []
    
    for item in data_container:
        new_item = item.copy()
        
        for old_key, new_key in cols.items():
            if old_key in new_item:
                new_item[new_key] = new_item.pop(old_key)
            else:
                new_item[new_key] = ''
        
        result.append(new_item)
    
    return result

def standardize_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standardize data for reporting by categorizing products by stock levels.
    
    This function processes the scraped data and organizes it into categories
    based on current stock levels. It also renames columns for consistency
    in reporting templates.
    
    Args:
        data: List of dictionaries containing product data
        
    Returns:
        Dict[str, Any]: Standardized data structure for reporting
        
    Example:
        >>> data = [{'Current stock': 0, 'product_name': 'Product A'}]
        >>> result = standardize_data(data)
        >>> 'out_of_stocks_products' in result['data']
        True
    """
    if not data:
        return {
            'data': {
                'out_of_stocks_products': [],
                'in_stocks_products': [],
                'more_5_stocks_products': [],
                'only_1_stocks_products': []
            }
        }
    
    # Column mapping for standardization
    column_mapping = {
        '1DroplistDesc': 'DroplistDesc1',
        '1DroplistValue': 'DroplistValue1',
        '2DroplistDesc': 'DroplistDesc2',
        '2DroplistValue': 'DroplistValue2',
        '3DroplistDesc': 'DroplistDesc3',
        '3DroplistValue': 'DroplistValue3',
        '4DroplistDesc': 'DroplistDesc4',
        '4DroplistValue': 'DroplistValue4'
    }
    
    # Categorize products by stock levels
    out_of_stock = [
        product_item for product_item in data 
        if product_item.get('Current stock', 0) == 0
    ]
    
    in_stock = [
        product_item for product_item in data 
        if product_item.get('Current stock', 0) > 0
    ]
    
    more_than_5_stock = [
        product_item for product_item in data 
        if product_item.get('Current stock', 0) > 5
    ]
    
    only_1_stock = [
        product_item for product_item in data 
        if product_item.get('Current stock', 0) == 1
    ]
    
    # Standardize data structure
    standard_data = {
        'data': {
            'out_of_stocks_products': rename_columns(out_of_stock, **column_mapping),
            'in_stocks_products': rename_columns(in_stock, **column_mapping),
            'more_5_stocks_products': rename_columns(more_than_5_stock, **column_mapping),
            'only_1_stocks_products': rename_columns(only_1_stock, **column_mapping)
        }
    }
    
    # Add summary statistics
    standard_data['summary'] = {
        'total_products': len(data),
        'out_of_stock_count': len(out_of_stock),
        'in_stock_count': len(in_stock),
        'low_stock_count': len(only_1_stock),
        'well_stocked_count': len(more_than_5_stock)
    }
    
    return standard_data

def validate_product_data(product_item: Dict[str, Any]) -> bool:
    """
    Validate that a product item contains required fields.
    
    Args:
        product_item: Dictionary containing product data
        
    Returns:
        bool: True if product data is valid, False otherwise
    """
    required_fields = ['product_name', 'Current stock']
    
    for field in required_fields:
        if field not in product_item:
            logging.warning(f"Missing required field: {field}")
            return False
    
    return True

def clean_product_data(product_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and normalize product data.
    
    Args:
        product_item: Dictionary containing product data
        
    Returns:
        Dict[str, Any]: Cleaned product data
    """
    cleaned_item = product_item.copy()
    
    # Ensure numeric fields are properly typed
    if 'Current stock' in cleaned_item:
        try:
            cleaned_item['Current stock'] = int(cleaned_item['Current stock'])
        except (ValueError, TypeError):
            cleaned_item['Current stock'] = 0
    
    if 'Previous stock' in cleaned_item:
        try:
            cleaned_item['Previous stock'] = int(cleaned_item['Previous stock'])
        except (ValueError, TypeError):
            cleaned_item['Previous stock'] = 0
    
    # Clean string fields
    for key, value in cleaned_item.items():
        if isinstance(value, str):
            cleaned_item[key] = value.strip()
    
    return cleaned_item


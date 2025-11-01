"""
Export Utilities for Black Eagle Arrows Inventory Scraper

This module provides export functionality for the Black Eagle Arrows inventory scraper.
It handles data export to various formats (CSV, Excel), report generation, and
hypertext creation for the output files.

The module includes functions for:
- Saving product descriptions to HTML files
- Exporting data to CSV format
- Generating HTML reports using Jinja2 templates
- Creating hyperlinks in Excel files
- Updating output files with previous stock information

Author: Project Developer
License: MIT
"""

from parsel import Selector 
from pathlib import Path 
from jinja2 import Environment, FileSystemLoader
from datetime import datetime 
from openpyxl.worksheet.hyperlink import Hyperlink
from utils.data_manipulation_utils import (
    standardize_data,
    clean_file_name
)
import pandas as pd 
import openpyxl 
import logging 
from typing import List, Dict, Any, Optional
import os

# Columns that uniquely identify a production variation
cols = [
    'SKU',
    '1DroplistDesc',
    '1DroplistValue',
    '2DroplistDesc',
    '2DroplistValue',
    '3DroplistDesc',
    '3DroplistValue',
    '4DroplistDesc',
    '4DroplistValue'
]

def save_description(selector: Selector, product_item: Dict[str, Any]) -> str:
    """
    Save product description to HTML file.
    
    This function extracts the product description from the page and saves it
    as an HTML file in the descriptions directory. The filename is cleaned
    to remove invalid characters.
    
    Args:
        selector: Parsel selector object containing the page content
        product_item: Dictionary containing product information including name
        
    Returns:
        str: Absolute path to the saved description file
        
    Raises:
        Exception: If there's an error writing the file
    """
    try:
        description_folder = Path(__file__).parents[1].joinpath('descriptions')
        description_folder.mkdir(exist_ok=True)
        
        description_path = description_folder.joinpath(clean_file_name(product_item['product_name']))
        description_content = product_item.get('Description', '')
        with open(description_path, 'w', encoding='utf-8') as file:
            file.write(description_content)
        
        return str(description_path.absolute())
        
    except Exception as e:
        logging.error(f"Error saving description for {product_item.get('product_name', 'Unknown')}: {e}")
        raise

def export(data: List[Dict[str, Any]]) -> None:
    """
    Export the extracted data to CSV file.
    
    This function saves the scraped data to a CSV file in the outputs directory.
    The data is converted to a pandas DataFrame before export.
    
    Args:
        data: List of dictionaries containing scraped product data
        
    Raises:
        Exception: If there's an error writing the CSV file
    """
    try:
        output_folder = Path(__file__).parents[1].joinpath('outputs')
        output_folder.mkdir(exist_ok=True)
        
        df = pd.DataFrame(data)
        output_path = output_folder.joinpath('output.csv')
        df.to_csv(output_path, index=False)
        
        logging.info(f"Exported {len(data)} records to {output_path}")
        
    except Exception as e:
        logging.error(f"Error exporting data to CSV: {e}")
        raise

def generate_report(template_name: str, data: List[Dict[str, Any]], logger: logging.RootLogger) -> None:
    """
    Generate HTML report using Jinja2 template.
    
    This function creates a comprehensive report from the scraped data using
    a Jinja2 template. The report includes inventory statistics and product details.
    
    Args:
        template_name: Name of the template file to use
        data: List of dictionaries containing scraped data
        logger: Logger instance for logging operations
        
    Raises:
        FileNotFoundError: If template file is not found
        Exception: If there's an error generating the report
    """
    try:
        logger.info('Generating reports...')
        
        # Create reports directory
        reports_dir = Path(__file__).parents[1].joinpath('reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Set up Jinja2 environment
        env = Environment(loader=FileSystemLoader('.'))
        
        # Load template
        if not os.path.exists(template_name):
            logger.warning(f"Template file {template_name} not found, using default template")
            template = env.get_template('template.txt')
        else:
            template = env.get_template(template_name)
        
        # Standardize data for reporting
        standardized_data = standardize_data(data)
        
        # Render report
        rendered_report = template.render(standardized_data)
        
        # Save report with timestamp
        timestamp = str(datetime.now()).replace(":", "-").replace(" ", "_")
        report_path = reports_dir.joinpath(f'report_{timestamp}.txt')
        
        with open(report_path, 'w', encoding='utf-8') as file:
            file.write(rendered_report)
        
        logger.info(f"Report generated: {report_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Template file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

def create_hypertext() -> None:
    """
    Create hyperlinks in the Excel output file.
    
    This function adds hyperlinks to the description files in the Excel output.
    It reads the Excel file and adds hyperlinks to the description column.
    
    Raises:
        FileNotFoundError: If the Excel file doesn't exist
        Exception: If there's an error processing the Excel file
    """
    try:
        excel_path = Path(__file__).parents[1].joinpath('outputs', 'output_final.xlsx')
        
        if not excel_path.exists():
            logging.warning("Excel file not found, skipping hyperlink creation")
            return
        
        workbook = openpyxl.load_workbook(str(excel_path))
        sheet = workbook.active
        
        # Add hyperlinks to description column (column R)
        for index, cell in enumerate(sheet['R'], start=1):
            if index == 1:  # Skip header row
                continue
            
            if cell.value and os.path.exists(str(cell.value)):
                cell.hyperlink = Hyperlink(
                    ref=f'R{index}',
                    target=str(cell.value),
                    display=str(cell.value)
                )
        
        workbook.save(str(excel_path))
        logging.info("Hyperlinks added to Excel file")
        
    except FileNotFoundError as e:
        logging.error(f"Excel file not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Error creating hyperlinks: {e}")
        raise

def update_output(data: List[Dict[str, Any]]) -> None:
    """
    Update the final output Excel file with processed data.
    
    This function compares new data with existing data to update previous stock
    information and creates a comprehensive Excel file with current and previous
    stock levels.
    
    Args:
        data: List of dictionaries containing scraped data
        
    Raises:
        Exception: If there's an error processing the data
    """
    try:
        output_dir = Path(__file__).parents[1].joinpath('outputs')
        output_dir.mkdir(exist_ok=True)
        
        excel_path = output_dir.joinpath('output_final.xlsx')
        csv_path = output_dir.joinpath('output.csv')
        
        # Check if previous Excel file exists
        if excel_path.exists() and csv_path.exists():
            try:
                # Load existing data
                old_df = pd.read_excel(str(excel_path), index_col=False).fillna('')
                new_df = pd.read_csv(str(csv_path), index_col=False).fillna('')
                
                # Update previous stock information
                for index, row in new_df.iterrows():
                    try:
                        # Find matching record in old data
                        mask = (
                            (old_df['SKU'] == row['SKU']) &
                            (old_df['1DroplistDesc'] == row['1DroplistDesc']) &
                            (old_df['1DroplistValue'] == row['1DroplistValue']) &
                            (old_df['2DroplistDesc'] == row['2DroplistDesc']) &
                            (old_df['2DroplistValue'] == row['2DroplistValue']) &
                            (old_df['3DroplistDesc'] == row['3DroplistDesc']) &
                            (old_df['3DroplistValue'] == row['3DroplistValue']) &
                            (old_df['4DroplistDesc'] == row['4DroplistDesc']) &
                            (old_df['4DroplistValue'] == row['4DroplistValue'])
                        )
                        
                        matching_stock = old_df[mask]['Current stock'].values
                        if len(matching_stock) > 0:
                            new_df.loc[index, 'Previous stock'] = matching_stock[0]
                            
                    except (IndexError, KeyError):
                        # No matching record found, keep default value
                        pass
                    
                    new_df.loc[index, 'Previous stock date'] = str(datetime.now())
                
                # Remove duplicates and save
                new_df.drop_duplicates(
                    subset=cols,
                    keep='last',
                    inplace=True
                )
                
                new_df.to_excel(str(excel_path), index=False)
                logging.info(f"Updated Excel file with {len(new_df)} records")
                
            except Exception as e:
                logging.error(f"Error updating existing Excel file: {e}")
                # Fallback to creating new file
                pd.DataFrame(data).to_excel(str(excel_path), index=False)
                
        else:
            # Create new Excel file
            pd.DataFrame(data).to_excel(str(excel_path), index=False)
            logging.info(f"Created new Excel file with {len(data)} records")
            
    except Exception as e:
        logging.error(f"Error updating output: {e}")
        raise
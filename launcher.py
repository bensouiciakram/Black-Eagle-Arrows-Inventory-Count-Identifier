"""
Black Eagle Arrows Inventory Count Identifier - Launcher

This module serves as the main entry point for the Black Eagle Arrows inventory scraper.
It handles user input, data initialization, and orchestrates the scraping process.

The launcher provides a user-friendly interface for configuring the scraper and
manages the overall execution flow.

Author: Project Developer
License: MIT
"""

from utils.logging_utils import (
    create_logger
) 
from utils.export_utils import (
    cols
) 
from utils.playwright_utils import main 
import pandas as pd 
import logging 
import os 
import pickle  
import asyncio 
from typing import List, Dict, Any, Set

# Global data containers
data: List[Dict[str, Any]] = []
failed_urls: Set[str] = set()
products_urls: Set[str] = set()
logger: logging.Logger = None

def get_user_configuration() -> tuple[int, bool]:
    """
    Get user configuration for the scraper.
    
    Returns:
        tuple[int, bool]: (number of concurrent tabs, headless mode)
    """
    try:
        pages_number = int(input('How many tabs do you want: '))
        if pages_number <= 0:
            print("Invalid number of tabs. Using default value of 5.")
            pages_number = 5
    except ValueError:
        print("Invalid input. Using default value of 5 tabs.")
        pages_number = 5
    
    headless_sign = input('Enter y if you want to see the browser and n if not: ').lower()
    headless = headless_sign != 'y'
    
    return pages_number, headless

def load_existing_data() -> None:
    """
    Load existing data from pickle file if available.
    
    This function checks for existing data.pkl file and loads it if found,
    otherwise initializes an empty data list.
    """
    global data, cols
    
    if os.path.exists('data.pkl'):
        try:
            df = pd.DataFrame(pickle.load(open('data.pkl', 'rb')))
            data = df[~df[cols].duplicated()].to_dict(orient='records')
            logger.info(f"Loaded {len(data)} existing records from data.pkl")
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
            data = []
    else:
        data = []
        logger.info("No existing data found, starting fresh")

def initialize_global_variables() -> None:
    """
    Initialize global variables and data structures.
    
    This function sets up the global variables used throughout the application,
    including data containers and configuration settings.
    """
    global data, failed_urls, products_urls, logger
    
    # Initialize logger
    logger = create_logger(logging.DEBUG)
    logger.info("Initializing Black Eagle Arrows Inventory Scraper")
    
    # Load existing data
    load_existing_data()
    
    # Initialize empty sets for tracking
    failed_urls = set()
    products_urls = set()
    
    logger.info("Global variables initialized successfully")

def main_launcher() -> None:
    """
    Main launcher function that orchestrates the scraping process.
    
    This function handles the complete workflow:
    1. Get user configuration
    2. Initialize global variables
    3. Run the main scraping process
    4. Handle any errors and cleanup
    """
    try:
        # Get user configuration
        pages_number, headless = get_user_configuration()
        
        # Initialize global variables
        initialize_global_variables()
        logger.info(f"Starting scraper with {pages_number} concurrent tabs, headless: {headless}")
        # Run the main scraping process
        asyncio.run(
            main(
                data,
                headless,
                pages_number,
                logger,
                failed_urls
            )
        )
        logger.info("Scraping process completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Scraping process interrupted by user")
        print("\nScraping interrupted. Progress has been saved.")
        
    except Exception as e:
        logger.error(f"Scraping process failed: {e}")
        print(f"\nAn error occurred: {e}")
        print("Check the logs for more details.")
        
    finally:
        # Save progress
        if data:
            try:
                pickle.dump(data, open('data.pkl', 'wb'))
                logger.info("Progress saved to data.pkl")
            except Exception as e:
                logger.error(f"Failed to save progress: {e}")

if __name__ == '__main__':
    main_launcher()
    

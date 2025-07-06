"""
Utils package for Black Eagle Arrows Inventory Count Identifier

This package contains utility modules for logging, data export, data manipulation,
and Playwright automation.

Modules:
    - logging_utils: Logging configuration and utilities
    - export_utils: Data export and report generation
    - data_manipulation_utils: Data processing and cleaning
    - playwright_utils: Browser automation utilities

Author: Project Developer
License: MIT
"""

from .logging_utils import create_logger, get_logger, set_log_level
from .export_utils import (
    save_description, 
    export, 
    generate_report, 
    create_hypertext, 
    update_output,
    cols
)
from .data_manipulation_utils import (
    format_date,
    clean_file_name,
    get_all_combinations,
    rename_columns,
    standardize_data,
    validate_product_data,
    clean_product_data
)
from .playwright_utils import (
    check_handled_url,
    get_total_pages,
    get_page_products_urls,
    get_product_item,
    handle_url,
    handle_listing,
    inventory_identifier,
    main
)

__all__ = [
    # Logging utilities
    'create_logger',
    'get_logger', 
    'set_log_level',
    
    # Export utilities
    'save_description',
    'export',
    'generate_report',
    'create_hypertext',
    'update_output',
    'cols',
    
    # Data manipulation utilities
    'format_date',
    'clean_file_name',
    'get_all_combinations',
    'rename_columns',
    'standardize_data',
    'validate_product_data',
    'clean_product_data',
    
    # Playwright utilities
    'check_handled_url',
    'get_total_pages',
    'get_page_products_urls',
    'get_product_item',
    'handle_url',
    'handle_listing',
    'inventory_identifier',
    'main'
]

__version__ = '2.0.0'
__author__ = 'Project Developer'
__license__ = 'MIT' 
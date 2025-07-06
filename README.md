# Black Eagle Arrows Inventory Count Identifier

A comprehensive web scraping automation tool for extracting product information and inventory quantities from blackeaglearrows.com. This project uses Playwright for browser automation and provides detailed inventory analysis with reporting capabilities.

## Features

- **Automated Product Scraping**: Extracts product information from multiple category pages
- **Inventory Detection**: Identifies stock quantities by testing cart additions
- **Multi-Variant Support**: Handles products with multiple attributes (size, color, etc.)
- **Concurrent Processing**: Supports multiple browser tabs for faster scraping
- **Progress Persistence**: Saves progress and can resume interrupted sessions
- **Comprehensive Reporting**: Generates detailed HTML reports with inventory statistics
- **Data Export**: Exports data to CSV and Excel formats with hyperlinks

## Project Structure

```
Black Eagle Arrows Inventory Count Identifier/
├── scraper.py              # Main scraping script with enhanced functionality
├── launcher.py             # User-friendly launcher with configuration
├── utils/                  # Utility modules
│   ├── logging_utils.py    # Logging configuration and utilities
│   ├── export_utils.py     # Data export and report generation
│   ├── data_manipulation_utils.py  # Data processing and cleaning
│   └── playwright_utils.py # Browser automation utilities
├── descriptions/           # Saved product descriptions (auto-generated)
├── outputs/               # Export files (auto-generated)
├── logs/                  # Log files (auto-generated)
├── reports/               # Generated reports (auto-generated)
└── requirements.txt       # Python dependencies
```

## Installation

1. **Clone or download the project**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

## Usage

### Quick Start

Run the launcher script for an interactive experience:

```bash
python launcher.py
```

The launcher will prompt you for:
- Number of concurrent browser tabs (recommended: 3-5)
- Whether to run in headless mode (y/n)

### Direct Execution

Run the main scraper directly:

```bash
python scraper.py
```

### Configuration

The scraper automatically handles:
- **URL Discovery**: Scrapes product URLs from listing pages
- **Data Persistence**: Saves progress to `data.pkl`
- **Error Recovery**: Tracks failed URLs for retry
- **Concurrent Processing**: Manages multiple browser instances

## Output Files

### Data Files
- `outputs/output.csv` - Raw scraped data in CSV format
- `outputs/output_final.xlsx` - Processed data with previous stock information
- `data.pkl` - Progress data for session resumption
- `products_urls.pkl` - Discovered product URLs
- `failed_urls.pkl` - URLs that failed to process

### Reports
- `reports/report_YYYY-MM-DD_HH-MM-SS.txt` - HTML reports with inventory analysis
- `logs/logs_YYYY-MM-DD_HH-MM-SS.log` - Detailed execution logs

### Product Descriptions
- `descriptions/` - HTML files containing product descriptions

## Data Schema

Each product record contains:

| Field | Description |
|-------|-------------|
| SKU | Product SKU code |
| Brand | Product brand |
| product_name | Product name |
| URL | Product page URL |
| 1DroplistDesc-4DroplistDesc | Attribute descriptions |
| 1DroplistValue-4DroplistValue | Attribute values |
| Price | Product price |
| Current stock | Current inventory quantity |
| Current stock date | Date of stock check |
| Previous stock | Previous inventory quantity |
| Previous stock date | Date of previous check |
| Description_path | Path to description HTML file |
| Description | Product description |
| Item photo URL | Product image URL |

## Advanced Features

### Inventory Detection Algorithm

The scraper uses a sophisticated algorithm to determine inventory levels:

1. **Initial Test**: Attempts to add a large quantity (default: 100)
2. **Binary Search**: If initial test fails, uses binary search to find maximum quantity
3. **Cart Response Analysis**: Monitors cart API responses for error messages
4. **Retry Logic**: Handles timeouts and network issues with automatic retries

### Multi-Variant Product Handling

For products with multiple attributes (e.g., size, color, material):
- Generates all possible combinations
- Tests inventory for each variant
- Creates separate records for each combination

### Progress Management

- **Session Resumption**: Can resume interrupted scraping sessions
- **Duplicate Prevention**: Avoids re-processing already scraped products
- **Error Tracking**: Maintains list of failed URLs for investigation

## Error Handling

The scraper includes comprehensive error handling:

- **Network Timeouts**: Automatic retry with exponential backoff
- **Page Load Failures**: Graceful handling of unavailable pages
- **Data Extraction Errors**: Logging and continuation on parsing failures
- **Browser Crashes**: Automatic browser restart and session recovery

## Performance Optimization

- **Concurrent Processing**: Multiple browser tabs for faster scraping
- **Resource Management**: Efficient memory usage and cleanup
- **Caching**: Saves discovered URLs to avoid re-discovery
- **Batch Processing**: Processes products in batches for better performance

## Monitoring and Logging

- **Real-time Logging**: Console and file logging with timestamps
- **Progress Tracking**: Regular updates on scraping progress
- **Error Reporting**: Detailed error messages with context
- **Performance Metrics**: Execution time and success rate tracking

## Troubleshooting

### Common Issues

1. **Browser Launch Failures**
   - Ensure Playwright is properly installed
   - Check system resources and available memory

2. **Network Timeouts**
   - Increase timeout values in the code
   - Check internet connection stability

3. **Memory Issues**
   - Reduce number of concurrent tabs
   - Restart the scraper periodically

4. **Data Corruption**
   - Delete `data.pkl` to start fresh
   - Check disk space availability

### Debug Mode

Enable debug logging by modifying the logging level in the code:

```python
logger = create_logger(logging.DEBUG)
```

## Contributing

When contributing to this project:

1. Follow the existing code style and documentation patterns
2. Add comprehensive docstrings to new functions
3. Include type annotations for all parameters and return values
4. Test changes with different product types and scenarios
5. Update this README for any new features or changes

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For issues and questions:
1. Check the logs for detailed error information
2. Review the troubleshooting section above
3. Ensure all dependencies are properly installed
4. Verify the target website is accessible

## Changelog

### Version 2.0 (Enhanced)
- Added comprehensive docstrings and type annotations
- Improved error handling and logging
- Enhanced data validation and cleaning
- Better modular code structure
- Added progress persistence and recovery
- Improved concurrent processing
- Enhanced reporting capabilities

### Version 1.0 (Original)
- Basic scraping functionality
- Inventory detection
- Data export to CSV/Excel
- Simple reporting 
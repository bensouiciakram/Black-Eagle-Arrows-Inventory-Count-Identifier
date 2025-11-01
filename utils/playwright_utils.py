"""
Playwright Utilities for Black Eagle Arrows Inventory Scraper

This module provides Playwright-based web scraping utilities for the Black Eagle Arrows
inventory scraper. It handles browser automation, page navigation, data extraction,
and inventory identification through cart testing.

The module includes functions for:
- Browser and page management
- Product URL extraction from listing pages
- Product data extraction
- Inventory quantity identification
- Concurrent task execution

Author: Project Developer
License: MIT
"""

from playwright.async_api import async_playwright, TimeoutError,Error
from playwright.async_api._generated import Browser
from playwright.async_api._generated import BrowserContext
from playwright.async_api._generated import Page
from playwright.async_api._generated import ElementHandle
from parsel import Selector 
from typing import List, Dict, Any, Set, Optional, Tuple
from copy import deepcopy 
from json.decoder import JSONDecodeError
from re import compile 
from utils.data_manipulation_utils import (
    get_all_combinations,
    format_date,
)
from utils.export_utils import (
    save_description,
    export,
    update_output,
    create_hypertext,
    generate_report
)
import pickle 
import asyncio 
import os 
import logging

# List of all available listing pages on the site
listing_urls = [
    'https://blackeaglearrows.com/bow-accessories/',
    'https://blackeaglearrows.com/arrows/',
    'https://blackeaglearrows.com/components/',
    'https://blackeaglearrows.com/gear/'
]

async def handle_help_us_stay_connected_popup(page:Page) :
    if await page.query_selector('//button[contains(@class,"needsclick")]'):
        await page.click('//button[contains(@class,"needsclick")]')

async def check_handled_url(page: Page, data: List[Dict[str, Any]]) -> bool:
    """
    Check if the URL has been processed before by comparing product combinations.
    
    Args:
        page: Playwright page object
        data: List of existing product data
        
    Returns:
        bool: True if URL has been handled, False otherwise
    """
    attrs_dict = await get_options_dict(page)
    all_combinations = get_all_combinations(*(attrs_dict.values()))
    return len(list(all_combinations)) == len([item['product_name'] == page.url for item in data])

async def get_total_pages(page: Page) -> int:
    """
    Get the total number of pages for a listing page.
    
    Args:
        page: Playwright page object
        
    Returns:
        int: Total number of pages, defaults to 1 if pagination not found
    """
    selector = Selector(text=await page.content())
    try:
        pagination_numbers = selector.xpath('//a[contains(@class,"listing-pagination-link")]').re(r'\d+')
        return max([int(number) for number in pagination_numbers]) if pagination_numbers else 1
    except ValueError:
        return 1

async def get_page_products_urls(page: Page) -> List[str]:
    """
    Extract all product URLs from a listing page.
    
    Args:
        page: Playwright page object
        
    Returns:
        List[str]: List of product URLs found on the page
    """
    selector = Selector(text=await page.content())
    return selector.xpath('//a[@class="card-figure__link"]/@href').getall()

async def get_description_outer_html(page:Page) -> str:
    """
    Extract the outer HTML of the product description section.
    
    Args:
        page: Playwright page object
        
    Returns:
        str: Outer HTML of the description section
    """
    desc_handle = await page.query_selector('//*[@id="tab-description"]')
    return await desc_handle.evaluate('(element) => element.outerHTML') if desc_handle else ''

async def get_product_item(page: Page) -> Dict[str, Any]:
    """
    Extract initial product information from a product page.
    
    Args:
        page: Playwright page object
        data: List of existing product data
        
    Returns:
        Dict[str, Any]: Dictionary containing product information
    """
    selector = Selector(text=await page.content())
    
    product_item = {
        'SKU': selector.xpath('string(//dt[@class="productView-info-name sku-label"]/following-sibling::dd[1])').get().strip(),
        'Brand': selector.xpath('string(//h2[@class="productView-brand"])').get().strip(),
        'product_name': selector.xpath('//h1/text()').get(),
        'URL': page.url,
        '1DroplistDesc': '',
        '1DroplistValue': '',
        '2DroplistDesc': '',
        '2DroplistValue': '',
        '3DroplistDesc': '',
        '3DroplistValue': '',
        '4DroplistDesc': '',
        '4DroplistValue': '',
        'Price': selector.xpath('string((//span[@class="price price--withoutTax"])[1])').get().strip(),
        'Current stock': 0,
        'Current stock date': format_date(),
        'Previous stock': 0,
        'Previous stock date': '',
        'Description_path': '',
        'Description': '',
        'Item photo URL': selector.xpath('//figure[@class="productView-image"]/@data-zoom-image').get()
    }
    
    # Save description and update paths
    product_item['Description'] = await get_description_outer_html(page)
    product_item['Description_path'] = save_description(selector, product_item)
    return product_item

async def handle_url(browser: Browser, url: str, logger: logging.RootLogger, 
                    data: List[Dict[str, Any]], failed_urls: Set[str]) -> None:
    """
    Handle the extraction logic for a single product URL.
    
    Args:
        browser: Playwright browser instance
        url: Product URL to process
        logger: Logger instance
        data: List of existing product data
        failed_urls: Set of failed URLs
    """
    context = await browser.new_context()
    context.set_default_timeout(5000)
    page = await context.new_page()
    
    try:
        await page.goto(url)
        
        if await check_handled_url(page, data):
            logger.info(f"URL already handled: {url}")
            return
        await handle_help_us_stay_connected_popup(page)
        primary_item = await get_product_item(page)
        
        # Check if product is unavailable
        unavailable_button = await page.query_selector('//div[@class="product-add-to-cart form-field"]/input[@value="Unavailable"]')
        if unavailable_button:
            logger.info('No adding cart button available')
            logger.info(f'Item scraped: {primary_item["product_name"]}')
            data.append(primary_item)
        else:
            try:
                await inventory_identifier(page, primary_item, logger, data)
            except TimeoutError:
                logger.error(f'Timeout problem in link: {url}')
                failed_urls.add(url)
                pickle.dump(failed_urls, open('failed_urls.pkl', 'wb'))
            except NotImplementedError:
                logger.error(f'NotImplementedError for link: {url}')
                failed_urls.add(url)
                pickle.dump(failed_urls, open('failed_urls.pkl', 'wb'))
                
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        failed_urls.add(url)
    finally:
        export(data)
        pickle.dump(data, open('data.pkl', 'wb'))
        await page.close()
        await context.close()

def load_products_urls() -> Set[str]:
    """
    Load existing product URLs from pickle file.
    
    Returns:
        Set[str]: Set of existing product URLs
    """
    if os.path.exists('products_urls.pkl'):
        return pickle.load(open('products_urls.pkl', 'rb'))
    else:
        return set()

async def handle_listing(browser: Browser, listing_url: str, logger: logging.RootLogger, 
                        data: List[Dict[str, Any]]) -> None:
    """
    Handle the listing page extraction logic to collect product URLs.
    
    Args:
        browser: Playwright browser instance
        listing_url: Listing page URL to process
        logger: Logger instance
        data: List of existing product data
    """
    context = await browser.new_context()
    context.set_default_timeout(5000)
    page = await context.new_page()
    
    try:
        await page.goto(listing_url)
        total_pages = await get_total_pages(page)
        
        logger.info(f'{total_pages} pages found for the listing URL {page.url}')
        await page.close()
        
        for page_id in range(1, total_pages + 1):
            listing_page_context = await browser.new_context()
            page = await listing_page_context.new_page()
            
            try:
                await page.goto(listing_url + f'?page={page_id}')
                products_urls = load_products_urls()
                new_urls = await get_page_products_urls(page)
                products_urls = products_urls.union(new_urls)
                pickle.dump(products_urls, open('products_urls.pkl', 'wb'))
                
                logger.info(f"Page {page_id}: Found {len(new_urls)} new products")
                
            except Exception as e:
                logger.error(f"Error processing page {page_id}: {e}")
            finally:
                await page.close()
                await listing_page_context.close()
                
    except Exception as e:
        logger.error(f"Error processing listing {listing_url}: {e}")
    finally:
        await context.close()

async def get_attr_values(attr_handle: ElementHandle) -> List[str]:
    """
    Extract attribute values from an attribute handle.
    
    Args:
        attr_handle: Playwright element handle for attribute
        
    Returns:
        List[str]: List of attribute values
    """
    options = await attr_handle.query_selector_all('//option')
    values = []
    
    for option in options:
        value = await option.get_attribute('value')
        if value:
            values.append(value)
    
    return values

async def get_options_dict(page: Page) -> Dict[ElementHandle, List[str]]:
    """
    Get dictionary of attribute handles and their available values.
    
    Args:
        page: Playwright page object
        
    Returns:
        Dict[ElementHandle, List[str]]: Dictionary mapping attribute handles to their values
    """
    attrs = await page.query_selector_all('//select[contains(@name,"attribute")]')
    attrs_values_dict = {}
    
    for attr in attrs:
        attrs_values_dict[attr] = await get_attr_values(attr)
    
    return attrs_values_dict

async def select_attr_option(option_handle: ElementHandle, attr_value: str) -> None:
    """
    Select an attribute option by value.
    
    Args:
        option_handle: Playwright element handle for option
        attr_value: Value to select
    """
    await option_handle.select_option(attr_value)

async def try_inventory_quantity(page: Page, check_value: int, logger: logging.RootLogger) -> bool:
    """
    Test if a specific quantity can be added to cart.
    
    Args:
        page: Playwright page object
        check_value: Quantity to test
        logger: Logger instance
        
    Returns:
        bool: True if quantity can be added, False otherwise
    """
    try:
        await page.fill('//input[@name="qty[]"]', str(check_value))
        
        count = 0
        while True:
            try:

                await page.click('//input[@id="form-action-addToCart"]')
                break
            except TimeoutError:
                count += 1
                if count % 5 == 0:
                    await page.reload()
                    continue
                
                logger.debug(f'Reclick attempt {count} for: {page.url}')
                continue
        
        async with page.expect_response('https://blackeaglearrows.com/remote/v1/cart/add') as response_value:
            response = await response_value.value
            response_obj = await response.json()
            
            try:
                if response_obj['data'].get('error'):
                    await page.click('//button[@class="confirm button"]')
                    return False
                else:
                    await page.click('//div[@id="previewModal"]//button[@class="modal-close"]')
                    return True
            except KeyError:
                return True
                
    except Exception as e:
        logger.error(f"Error testing inventory quantity {check_value}: {e}")
        raise TimeoutError # todo later delete this 
        return False
    
async def check_out_of_stock(page: Page) -> bool:
    availability_handle = await page.query_selector(
        '//dt[contains(text(),"Availability:")]'
        '/following-sibling::dd[@class="productView-info-value"]'
    )
    if availability_handle is None :
        return False 
    return 'out of Stock' in await availability_handle.inner_text()
    

async def get_inventory_value(page: Page, check_value: int, logger: logging.RootLogger) -> int:
    """
    Get the actual inventory value by testing quantities.
    
    Args:
        page: Playwright page object
        check_value: Initial quantity to check
        logger: Logger instance
        
    Returns:
        int: Actual inventory quantity
    """

    inventory = 0
    try_count = 0
    
    if await check_out_of_stock(page):
        return inventory 
    
    while True:
        try_count += 1
        
        if try_count > 10:
            check_value += 50000
            try_count = -100000

        availability = await try_inventory_quantity(page, check_value, logger)
        
        if availability:
            inventory += check_value
        else:
            check_value = check_value // 2
            
        if check_value == 1 and not availability:
            break
    
    return inventory

async def get_attr_value(page: Page, attr_value: str) -> str:
    """
    Get attribute value from page.
    
    Args:
        page: Playwright page object
        attr_value: Attribute value to extract
        
    Returns:
        str: Extracted attribute value
    """
    return attr_value

async def get_select_desc(handle:ElementHandle) -> str:
    """
    Get the description of a select attribute.
    
    Args:
        handle: Playwright element handle for select attribute
        
    Returns:
        str: label of the select attribute
    """
    desc_handle = await handle.query_selector('xpath=.//preceding-sibling::label')
    desc = await desc_handle.inner_text()
    return desc.split(':')[0] if desc else ''

async def inventory_identifier(page: Page, primary_item: Dict[str, Any], 
                             logger: logging.RootLogger, data: List[Dict[str, Any]], 
                             guessed_initial_value: int = 100) -> int:
    """
    Identify inventory quantity for a product by testing cart additions.
    
    Args:
        page: Playwright page object
        primary_item: Primary product item dictionary
        logger: Logger instance
        data: List of existing product data
        guessed_initial_value: Initial guess for inventory quantity
        
    Returns:
        int: Number of product variations processed
    """
    attrs_dict = await get_options_dict(page)
    if not attrs_dict:
        raise NotImplementedError("handling pages with no select inside will be added later")
    all_combinations = get_all_combinations(*(attrs_dict.values()))
    for combination in all_combinations:
        # Select attributes
        attr_handles = list(attrs_dict.keys())
        if len(attr_handles) > 1:
            for i, (attr_handle, value) in enumerate(zip(attr_handles, combination)):
                await select_attr_option(attr_handle, value)
                await page.wait_for_timeout(500)
        elif len(attr_handles) == 1:
            for attr_handle,values in attrs_dict.items():
                for value in combination:
                    await select_attr_option(attr_handle, value)
                    await page.wait_for_timeout(500)
        # Create product variation item
        variation_item = deepcopy(primary_item)
        variation_item.update(await get_product_item(page))
        attr_names = [await get_select_desc(handle) for handle in attrs_dict.keys()]
        for i, (attr_name, attr_value) in enumerate(zip(attr_names, combination)):
            variation_item[f'{i+1}DroplistDesc'] = str(attr_name)
            variation_item[f'{i+1}DroplistValue'] = attr_value
        # Test inventory quantity
        inventory_quantity = await get_inventory_value(page, guessed_initial_value, logger)
        variation_item['Current stock'] = inventory_quantity
        
        logger.info(f"Product variation: {variation_item['product_name']} - Stock: {inventory_quantity}")
        data.append(variation_item)
    
    return len(all_combinations)

async def gather_with_concurrency(n: int, *tasks) -> List[Any]:
    """
    Run tasks with limited concurrency.
    
    Args:
        n: Maximum number of concurrent tasks
        *tasks: Tasks to execute
        
    Returns:
        List[Any]: Results from all tasks
    """
    semaphore = asyncio.Semaphore(n)
    
    async def sem_task(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*(sem_task(task) for task in tasks))

async def run(p, data: List[Dict[str, Any]], headless: bool, pages_number: int, 
             logger: logging.RootLogger, failed_urls: Set[str]) -> None:
    """
    Main execution function for the scraper.
    
    Args:
        p: Playwright instance
        data: List of existing product data
        headless: Whether to run browser in headless mode
        pages_number: Number of concurrent pages
        logger: Logger instance
        failed_urls: Set of failed URLs
    """
    browser = await p.chromium.launch(headless=headless)
    
    try:
        # First, collect all product URLs from listing pages
        listing_tasks = [handle_listing(browser, url, logger, data) for url in list(listing_urls)]
        await gather_with_concurrency(2, *listing_tasks)
        
        # Load collected URLs
        products_urls = load_products_urls()
        logger.info(f"Collected {len(products_urls)} product URLs")

        # Then process each product URL
        product_tasks = [handle_url(browser, url, logger, data, failed_urls) for url in list(products_urls)]
        await gather_with_concurrency(pages_number, *product_tasks)
        
    finally:
        await browser.close()

async def main(*args) -> None:
    """
    Main entry point for the Black Eagle Arrows scraper.
    
    Args:
        *args: Variable arguments (data, headless, pages_number, logger, failed_urls)
    """
    data, headless, pages_number, logger, failed_urls = args
    try:
        async with async_playwright() as p:
            await run(p, data, headless, pages_number, logger, failed_urls)
        
        # Generate final outputs
        update_output(data)
        create_hypertext()
        
        # Generate report
        if os.path.exists('template.txt'):
            generate_report('template.txt', data, logger)
        
        logger.info("Scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise 
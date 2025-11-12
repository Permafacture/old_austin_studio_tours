#!/usr/bin/env python3
"""
Austin Studio Tour Map Scraper - Selenium Version
Extracts location data from the Austin Studio Tour map using Selenium
to handle JavaScript-loaded content and saves to CSV
"""

import json
import csv
import time
import re
from typing import List, Dict, Any

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not installed. Install with: pip install selenium")


class AustinStudioTourSeleniumScraper:
    """Scraper for Austin Studio Tour locations using Selenium"""

    def __init__(self, headless: bool = True):
        self.base_url = "https://www.atxstudiotour.com"
        self.map_url = "https://www.atxstudiotour.com/explore/?view=map"
        self.headless = headless
        self.driver = None

    def init_driver(self):
        """Initialize Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium is not installed. Install with: pip install selenium")

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        self.driver = webdriver.Chrome(options=chrome_options)

    def extract_markers_from_map(self) -> List[Dict[str, Any]]:
        """
        Load the map page and extract marker data from JavaScript
        """
        if not self.driver:
            self.init_driver()

        print("Loading map page with Selenium...")
        self.driver.get(self.map_url)

        # Wait for map to load
        print("Waiting for map to load...")
        time.sleep(5)  # Give time for all JavaScript to execute

        markers = []

        # Method 1: Try to extract from window object or global variables
        print("Attempting to extract marker data from JavaScript...")

        # Try to get map markers from various global objects
        js_extraction_attempts = [
            # Try to get Google Maps markers
            """
            var markers = [];
            if (window.google && window.google.maps) {
                // Try to find map instance
                for (var prop in window) {
                    if (window[prop] && window[prop].markers) {
                        markers = window[prop].markers;
                        break;
                    }
                }
            }
            return markers;
            """,
            # Try to get data from JetEngine
            """
            var data = [];
            if (window.JetEngineSettings && window.JetEngineSettings.maps) {
                data = window.JetEngineSettings.maps;
            }
            return data;
            """,
            # Try to extract from data attributes
            """
            var markers = [];
            var mapElements = document.querySelectorAll('[data-lat], [data-lng]');
            mapElements.forEach(function(el) {
                markers.push({
                    lat: el.getAttribute('data-lat'),
                    lng: el.getAttribute('data-lng'),
                    title: el.getAttribute('data-title') || el.textContent
                });
            });
            return markers;
            """,
        ]

        for script in js_extraction_attempts:
            try:
                result = self.driver.execute_script(script)
                if result and len(result) > 0:
                    print(f"Successfully extracted {len(result)} markers!")
                    markers = result
                    break
            except Exception as e:
                print(f"Extraction attempt failed: {e}")

        # Method 2: Look for marker elements in the DOM
        if not markers:
            print("Trying to find markers in DOM elements...")
            try:
                marker_elements = self.driver.find_elements(By.CSS_SELECTOR, '.jet-map-marker, .marker, [class*="marker"]')
                print(f"Found {len(marker_elements)} potential marker elements")

                for elem in marker_elements:
                    try:
                        # Try to get data from element
                        data_attrs = self.driver.execute_script(
                            "return arguments[0].dataset;", elem
                        )
                        if data_attrs:
                            markers.append(data_attrs)
                    except:
                        pass
            except Exception as e:
                print(f"DOM extraction failed: {e}")

        # Method 3: Intercept network requests (capture AJAX responses)
        print("Checking browser logs for network activity...")
        try:
            logs = self.driver.get_log('performance')
            for entry in logs:
                log = json.loads(entry['message'])['message']
                if log['method'] == 'Network.responseReceived':
                    response_url = log['params']['response']['url']
                    if 'location' in response_url.lower() or 'marker' in response_url.lower():
                        print(f"Found relevant network request: {response_url}")
        except Exception as e:
            print(f"Log checking failed: {e}")

        return markers

    def scrape_location_pages(self, max_locations: int = None) -> List[Dict[str, Any]]:
        """
        Scrape individual location pages to get addresses
        """
        if not self.driver:
            self.init_driver()

        locations = []

        # First, get list of location URLs
        print("Getting list of locations...")
        self.driver.get("https://www.atxstudiotour.com/explore/?view=list")
        time.sleep(3)

        # Find all location links
        links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/location/"]')
        location_urls = list(set([link.get_attribute('href') for link in links if link.get_attribute('href')]))

        if max_locations:
            location_urls = location_urls[:max_locations]

        print(f"Found {len(location_urls)} location URLs")

        for i, url in enumerate(location_urls, 1):
            if i % 10 == 0:
                print(f"Processing location {i}/{len(location_urls)}...")

            try:
                self.driver.get(url)
                time.sleep(1)

                # Extract data from the page
                location_data = {
                    'url': url,
                    'title': '',
                    'address': '',
                    'latitude': '',
                    'longitude': ''
                }

                # Get title
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1, .entry-title, .location-title')
                    location_data['title'] = title_elem.text.strip()
                except:
                    # Extract from URL
                    location_data['title'] = url.split('/')[-2].replace('-', ' ').title()

                # Look for address in page text
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                address_match = re.search(
                    r'\d+\s+[A-Za-z0-9\s,\.]+,\s*Austin,?\s*TX\s*\d{5}(?:-\d{4})?,?\s*USA',
                    page_text
                )
                if address_match:
                    location_data['address'] = address_match.group(0).strip()

                # Try to extract coordinates from scripts or map elements
                coords_script = """
                var lat = '', lng = '';
                // Look in data attributes
                var mapElems = document.querySelectorAll('[data-lat], [data-latitude]');
                if (mapElems.length > 0) {
                    lat = mapElems[0].getAttribute('data-lat') || mapElems[0].getAttribute('data-latitude');
                }
                var lngElems = document.querySelectorAll('[data-lng], [data-longitude]');
                if (lngElems.length > 0) {
                    lng = lngElems[0].getAttribute('data-lng') || lngElems[0].getAttribute('data-longitude');
                }
                return {lat: lat, lng: lng};
                """
                try:
                    coords = self.driver.execute_script(coords_script)
                    if coords['lat']:
                        location_data['latitude'] = coords['lat']
                    if coords['lng']:
                        location_data['longitude'] = coords['lng']
                except:
                    pass

                locations.append(location_data)

            except Exception as e:
                print(f"Error processing {url}: {e}")

        return locations

    def save_to_csv(self, locations: List[Dict[str, str]], filename: str = 'austin_studio_tour_locations.csv'):
        """Save locations to a CSV file"""
        if not locations:
            print("No locations to save!")
            return

        print(f"Saving {len(locations)} locations to {filename}...")

        # Get all unique keys
        fieldnames = set()
        for loc in locations:
            fieldnames.update(loc.keys())
        fieldnames = sorted(list(fieldnames))

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(locations)

        print(f"Successfully saved to {filename}")

    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()


def main():
    """Main execution function"""
    if not SELENIUM_AVAILABLE:
        print("\n❌ Selenium is not installed!")
        print("\nInstall with: pip install selenium")
        print("You'll also need Chrome browser and ChromeDriver installed.")
        print("\nFor Ubuntu/Debian:")
        print("  sudo apt-get update")
        print("  sudo apt-get install -y chromium-browser chromium-chromedriver")
        print("\nOr use: pip install webdriver-manager")
        return

    scraper = AustinStudioTourSeleniumScraper(headless=True)

    try:
        print("Starting Austin Studio Tour scraper with Selenium...")
        print("=" * 60)

        # Try to get markers from map first
        markers = scraper.extract_markers_from_map()

        if markers:
            print(f"\n✅ Extracted {len(markers)} markers from map!")
            print("\nSample marker:")
            print(json.dumps(markers[0], indent=2))
            scraper.save_to_csv(markers)
        else:
            print("\n⚠️ Could not extract markers from map JavaScript.")
            print("Falling back to scraping individual location pages...")

            # Scrape individual location pages
            locations = scraper.scrape_location_pages(max_locations=10)  # Test with 10 first

            if locations:
                print(f"\n✅ Scraped {len(locations)} locations!")
                print("\nSample location:")
                print(json.dumps(locations[0], indent=2))
                scraper.save_to_csv(locations)
            else:
                print("\n❌ No location data found!")

    finally:
        scraper.close()

    print("\n✅ Scraping complete!")


if __name__ == "__main__":
    main()

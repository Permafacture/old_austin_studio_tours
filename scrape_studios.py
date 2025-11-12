#!/usr/bin/env python3
"""
Austin Studio Tour Map Scraper
Extracts location data from the Austin Studio Tour map and saves to CSV
"""

import requests
import json
import csv
import re
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from urllib.parse import urljoin


class AustinStudioTourScraper:
    """Scraper for Austin Studio Tour locations"""

    def __init__(self):
        self.base_url = "https://www.atxstudiotour.com"
        self.map_url = "https://www.atxstudiotour.com/explore/?view=map"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_from_html(self) -> List[Dict[str, Any]]:
        """
        Try to extract location data from embedded JSON in the HTML page
        """
        print("Fetching map page HTML...")
        response = self.session.get(self.map_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        locations = []

        # Look for JSON data in script tags
        script_tags = soup.find_all('script')

        for script in script_tags:
            if script.string:
                # Look for JetEngine map data or similar structures
                if 'jet-engine' in script.string or 'locations' in script.string.lower():
                    # Try to extract JSON objects
                    json_matches = re.findall(r'\{[^{}]*"lat"[^{}]*"lng"[^{}]*\}', script.string)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            locations.append(data)
                        except json.JSONDecodeError:
                            continue

                # Also look for marker data
                if 'marker' in script.string.lower() or 'coordinates' in script.string.lower():
                    print(f"Found potential data in script: {script.string[:200]}...")

        return locations

    def scrape_via_rest_api(self) -> List[Dict[str, Any]]:
        """
        Try to get location data via WordPress REST API
        """
        print("Trying WordPress REST API...")
        locations = []
        page = 1
        per_page = 100

        while True:
            url = f"{self.base_url}/wp-json/wp/v2/location"
            params = {
                'per_page': per_page,
                'page': page,
                '_embed': True
            }

            response = self.session.get(url, params=params)

            if response.status_code != 200:
                break

            data = response.json()

            if not data:
                break

            locations.extend(data)

            # Check if there are more pages
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if page >= total_pages:
                break

            page += 1
            print(f"Fetched page {page-1}/{total_pages}...")

        return locations

    def try_ajax_endpoints(self) -> List[Dict[str, Any]]:
        """
        Try various AJAX endpoints that might return location data
        """
        print("Trying AJAX endpoints...")

        # Common WordPress AJAX actions for JetEngine
        ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"

        # Try different action parameters
        actions = [
            'jet_engine_ajax',
            'jet_engine_get_listings',
            'jet_smart_filters',
            'get_map_markers',
        ]

        for action in actions:
            try:
                response = self.session.post(ajax_url, data={
                    'action': action,
                    'query_id': '52',  # Map query ID from earlier analysis
                    'listing_id': '14109',  # Map listing ID
                })

                if response.status_code == 200 and response.text:
                    print(f"Action '{action}' returned data: {response.text[:200]}")
                    try:
                        data = response.json()
                        if data:
                            return data if isinstance(data, list) else [data]
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print(f"Error trying action {action}: {e}")

        return []

    def extract_address_from_page(self, url: str) -> tuple[str, str, str]:
        """
        Extract address and coordinates from an individual location page
        Returns: (address, latitude, longitude)
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for address in various places
            address = ""
            lat = ""
            lng = ""

            # Method 1: Look for address in text content
            address_pattern = r'\d+\s+[A-Za-z0-9\s,\.]+,\s*Austin,?\s*TX\s*\d{5}(?:-\d{4})?,?\s*USA'
            text = soup.get_text()
            address_match = re.search(address_pattern, text)
            if address_match:
                address = address_match.group(0).strip()

            # Method 2: Look for coordinates in script tags or data attributes
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string:
                    # Look for lat/lng in various formats
                    lat_match = re.search(r'"lat":\s*(-?\d+\.\d+)', script.string)
                    lng_match = re.search(r'"lng":\s*(-?\d+\.\d+)', script.string)

                    if not lat_match:
                        lat_match = re.search(r'"latitude":\s*(-?\d+\.\d+)', script.string)
                    if not lng_match:
                        lng_match = re.search(r'"longitude":\s*(-?\d+\.\d+)', script.string)

                    if lat_match and not lat:
                        lat = lat_match.group(1)
                    if lng_match and not lng:
                        lng = lng_match.group(1)

            # Method 3: Look in meta tags
            if not address:
                # Check various meta tags that might contain address
                address_metas = soup.find_all('meta', {'property': re.compile(r'.*address.*', re.I)})
                for meta in address_metas:
                    if meta.get('content'):
                        address = meta['content']
                        break

            return address, lat, lng

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return "", "", ""

    def parse_location_data(self, raw_locations: List[Dict[str, Any]], fetch_addresses: bool = True) -> List[Dict[str, str]]:
        """
        Parse raw location data into a standardized format
        If fetch_addresses is True, will fetch each location page to get addresses
        """
        parsed_locations = []
        total = len(raw_locations)

        for i, loc in enumerate(raw_locations, 1):
            parsed = {
                'id': loc.get('id', ''),
                'title': '',
                'address': '',
                'latitude': '',
                'longitude': '',
                'location_type': '',
                'url': ''
            }

            # Extract title
            if 'title' in loc:
                if isinstance(loc['title'], dict):
                    parsed['title'] = loc['title'].get('rendered', '')
                else:
                    parsed['title'] = str(loc['title'])

            # Extract coordinates from API data first
            if 'lat' in loc:
                parsed['latitude'] = loc['lat']
            if 'lng' in loc or 'lon' in loc:
                parsed['longitude'] = loc.get('lng', loc.get('lon', ''))

            # Extract address from API data
            if 'address' in loc:
                parsed['address'] = loc['address']

            # Extract URL
            if 'link' in loc:
                parsed['url'] = loc['link']

            # Extract location type
            if 'location-type' in loc and loc['location-type']:
                parsed['location_type'] = str(loc['location-type'])

            # If we don't have address/coordinates and we have a URL, fetch the page
            if fetch_addresses and parsed['url'] and not parsed['address']:
                if i % 10 == 0 or i == total:
                    print(f"Fetching addresses: {i}/{total}...")

                address, lat, lng = self.extract_address_from_page(parsed['url'])

                if address and not parsed['address']:
                    parsed['address'] = address
                if lat and not parsed['latitude']:
                    parsed['latitude'] = lat
                if lng and not parsed['longitude']:
                    parsed['longitude'] = lng

                # Rate limiting - be nice to the server
                time.sleep(0.2)

            parsed_locations.append(parsed)

        return parsed_locations

    def save_to_csv(self, locations: List[Dict[str, str]], filename: str = 'austin_studio_tour_locations.csv'):
        """
        Save locations to a CSV file
        """
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

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method - tries multiple approaches
        """
        locations = []

        # Try method 1: HTML embedded data
        print("\n=== Method 1: Scraping HTML for embedded data ===")
        html_locations = self.scrape_from_html()
        if html_locations:
            print(f"Found {len(html_locations)} locations in HTML")
            locations.extend(html_locations)

        # Try method 2: AJAX endpoints
        if not locations:
            print("\n=== Method 2: Trying AJAX endpoints ===")
            ajax_locations = self.try_ajax_endpoints()
            if ajax_locations:
                print(f"Found {len(ajax_locations)} locations via AJAX")
                locations.extend(ajax_locations)

        # Try method 3: REST API (gets location posts but may not have coordinates)
        if not locations:
            print("\n=== Method 3: Using REST API ===")
            api_locations = self.scrape_via_rest_api()
            if api_locations:
                print(f"Found {len(api_locations)} locations via REST API")
                locations.extend(api_locations)

        return locations


def main():
    """Main execution function"""
    scraper = AustinStudioTourScraper()

    print("Starting Austin Studio Tour scraper...")
    print("=" * 60)

    # Scrape the data
    raw_locations = scraper.scrape()

    if not raw_locations:
        print("\n❌ No location data found!")
        print("\nThis site likely requires JavaScript execution to load map data.")
        print("Consider using Selenium or Playwright for a headless browser approach.")
        return

    # Parse and save
    print(f"\n=== Processing {len(raw_locations)} locations ===")
    parsed_locations = scraper.parse_location_data(raw_locations)

    # Show sample
    if parsed_locations:
        print("\nSample location:")
        print(json.dumps(parsed_locations[0], indent=2))

    # Save to CSV
    scraper.save_to_csv(parsed_locations)

    print("\n✅ Scraping complete!")


if __name__ == "__main__":
    main()

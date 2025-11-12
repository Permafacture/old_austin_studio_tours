#!/usr/bin/env python3
"""
Austin Studio Tour Map Scraper - Enhanced Version
Uses requests-html for lightweight JavaScript execution to get addresses
Falls back to requests-only for basic data if requests-html not available
"""

import requests
import json
import csv
import time
import re
from typing import List, Dict, Any

try:
    from requests_html import HTMLSession
    REQUESTS_HTML_AVAILABLE = True
except ImportError:
    REQUESTS_HTML_AVAILABLE = False
    print("Note: requests-html not available. Install with: pip install requests-html")
    print("Falling back to requests-only mode (no addresses/coordinates)\n")


class AustinStudioTourScraper:
    """Scraper for Austin Studio Tour locations"""

    def __init__(self, use_js: bool = True):
        self.base_url = "https://www.atxstudiotour.com"
        self.use_js = use_js and REQUESTS_HTML_AVAILABLE

        if self.use_js:
            self.session = HTMLSession()
        else:
            self.session = requests.Session()

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'{self.base_url}/explore/?view=map',
        })

    def get_all_locations_basic(self) -> List[Dict[str, Any]]:
        """
        Get basic location data from WordPress REST API (no addresses)
        """
        print("Fetching location list from WordPress API...")

        # First visit map page to get cookies
        self.session.get(f'{self.base_url}/explore/?view=map')

        locations = []
        page = 1
        per_page = 100

        while True:
            url = f"{self.base_url}/wp-json/wp/v2/location"
            params = {
                'per_page': per_page,
                'page': page,
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
            print(f"Fetched page {page-1}/{total_pages} ({len(locations)} locations so far)...")

        return locations

    def extract_address_with_js(self, url: str) -> tuple[str, str, str]:
        """
        Extract address and coordinates using JavaScript rendering
        Returns: (address, latitude, longitude)
        """
        if not self.use_js:
            return "", "", ""

        try:
            response = self.session.get(url)

            # Render JavaScript
            response.html.render(timeout=20, sleep=2)

            address = ""
            lat = ""
            lng = ""

            # Method 1: Look for address in rendered text
            text = response.html.text
            address_match = re.search(
                r'\d+\s+[A-Za-z0-9\s,\.]+,\s*Austin,?\s*TX\s*\d{5}(?:-\d{4})?,?\s*USA',
                text
            )
            if address_match:
                address = address_match.group(0).strip()

            # Method 2: Check for data attributes after JS execution
            for elem in response.html.find('[data-lat]'):
                lat = elem.attrs.get('data-lat', '')
                lng = elem.attrs.get('data-lng', '')
                if lat and lng:
                    break

            # Method 3: Check for address in data attributes
            for elem in response.html.find('[data-address]'):
                if not address:
                    address = elem.attrs.get('data-address', '')
                    break

            return address, lat, lng

        except Exception as e:
            print(f"Error rendering {url}: {e}")
            return "", "", ""

    def scrape_with_addresses(self, max_locations: int = None) -> List[Dict[str, str]]:
        """
        Scrape all locations with addresses (requires requests-html)
        """
        if not self.use_js:
            print("JavaScript execution not available. Use: pip install requests-html")
            print("Falling back to basic data only...\n")
            return self.scrape_basic()

        print("Scraping locations with JavaScript rendering...")
        print("This will take a while as we need to render each page...\n")

        # Get basic location data first
        raw_locations = self.get_all_locations_basic()

        if max_locations:
            raw_locations = raw_locations[:max_locations]

        locations = []
        total = len(raw_locations)

        for i, loc in enumerate(raw_locations, 1):
            location_data = {
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
                    location_data['title'] = loc['title'].get('rendered', '')
                else:
                    location_data['title'] = str(loc['title'])

            # Extract URL
            if 'link' in loc:
                location_data['url'] = loc['link']

            # Extract location type
            if 'location-type' in loc and loc['location-type']:
                location_data['location_type'] = str(loc['location-type'])

            # Fetch address with JavaScript rendering
            if location_data['url']:
                if i % 10 == 0 or i == total:
                    print(f"Processing location {i}/{total}...")

                address, lat, lng = self.extract_address_with_js(location_data['url'])

                if address:
                    location_data['address'] = address
                if lat:
                    location_data['latitude'] = lat
                if lng:
                    location_data['longitude'] = lng

                # Rate limiting
                time.sleep(0.5)

            locations.append(location_data)

        return locations

    def scrape_basic(self) -> List[Dict[str, str]]:
        """
        Scrape basic location data without addresses (requests-only)
        """
        print("Scraping basic location data (no addresses)...\n")

        raw_locations = self.get_all_locations_basic()
        locations = []

        for loc in raw_locations:
            location_data = {
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
                    location_data['title'] = loc['title'].get('rendered', '')
                else:
                    location_data['title'] = str(loc['title'])

            # Extract URL
            if 'link' in loc:
                location_data['url'] = loc['link']

            # Extract location type
            if 'location-type' in loc and loc['location-type']:
                location_data['location_type'] = str(loc['location-type'])

            locations.append(location_data)

        return locations

    def save_to_csv(self, locations: List[Dict[str, str]], filename: str = 'austin_studio_tour_locations.csv'):
        """Save locations to a CSV file"""
        if not locations:
            print("No locations to save!")
            return

        print(f"\nSaving {len(locations)} locations to {filename}...")

        # Get all unique keys
        fieldnames = set()
        for loc in locations:
            fieldnames.update(loc.keys())
        fieldnames = sorted(list(fieldnames))

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(locations)

        print(f"✓ Successfully saved to {filename}")


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape Austin Studio Tour locations')
    parser.add_argument('--with-addresses', action='store_true',
                        help='Include addresses (requires requests-html, slower)')
    parser.add_argument('--max-locations', type=int, default=None,
                        help='Maximum number of locations to process (for testing)')
    parser.add_argument('--output', type=str, default='austin_studio_tour_locations.csv',
                        help='Output CSV filename')

    args = parser.parse_args()

    print("=" * 60)
    print("Austin Studio Tour Map Scraper")
    print("=" * 60)

    scraper = AustinStudioTourScraper(use_js=args.with_addresses)

    # Scrape the data
    if args.with_addresses:
        if not REQUESTS_HTML_AVAILABLE:
            print("\n⚠ requests-html not installed!")
            print("Install with: pip install requests-html")
            print("Falling back to basic scraping...\n")
            locations = scraper.scrape_basic()
        else:
            print(f"\nScraping WITH addresses (using JavaScript rendering)")
            if args.max_locations:
                print(f"Limited to first {args.max_locations} locations for testing\n")
            locations = scraper.scrape_with_addresses(max_locations=args.max_locations)
    else:
        print("\nScraping basic data only (no addresses)\n")
        locations = scraper.scrape_basic()

    if locations:
        print(f"\n✓ Scraped {len(locations)} locations")

        # Show sample
        print("\nSample location:")
        print(json.dumps(locations[0], indent=2))

        # Check if we got addresses
        with_addresses = sum(1 for loc in locations if loc.get('address'))
        if with_addresses:
            print(f"\n✓ {with_addresses}/{len(locations)} locations have addresses")
        else:
            print("\n⚠ No addresses found (use --with-addresses to get them)")

        # Save to CSV
        scraper.save_to_csv(locations, args.output)
    else:
        print("\n❌ No location data found!")

    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

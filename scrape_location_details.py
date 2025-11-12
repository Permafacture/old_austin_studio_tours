#!/usr/bin/env python3
"""
Austin Studio Tour Location Details Scraper
Scrapes individual location pages to extract:
- Location number
- Address
- Hosts (with images and links)
- Artists (with images and links)
"""

import requests
import csv
import time
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple


class LocationDetailsScraper:
    """Scraper for detailed location information"""

    def __init__(self):
        self.base_url = "https://www.atxstudiotour.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_all_location_urls(self) -> List[Dict[str, str]]:
        """
        Get all location URLs from the WordPress API
        """
        print("Fetching location list from WordPress API...")

        # Visit map page to get cookies
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

            for loc in data:
                locations.append({
                    'id': loc.get('id', ''),
                    'url': loc.get('link', '')
                })

            # Check if there are more pages
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if page >= total_pages:
                break

            page += 1

        print(f"Found {len(locations)} locations\n")
        return locations

    def extract_location_details(self, url: str) -> Dict[str, str]:
        """
        Extract detailed information from a location page
        Returns dict with: number, address, hosts, artists
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            details = {
                'number': '',
                'address': '',
                'hosts': '',
                'artists': ''
            }

            # Extract location number from h1
            h1 = soup.find('h1')
            if h1:
                # Remove the trailing period if present
                details['number'] = h1.get_text().strip().rstrip('.')

            # Extract address using regex pattern
            address_pattern = r'\d+\s+[NSEW]?\s*[A-Za-z\s]+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Rd|Road|Ln|Lane|Way|Pkwy|Parkway|Ct|Court|Pl|Place),\s*Austin,?\s*TX\s*\d{5}'

            # Look for address in h2 elements (most reliable)
            for h2 in soup.find_all('h2', class_='elementor-heading-title'):
                text = h2.get_text(separator=' ', strip=True)
                match = re.search(address_pattern, text, re.IGNORECASE)
                if match:
                    details['address'] = match.group(0)
                    break

            # Extract hosts
            hosts = self._extract_participants(soup, 'Featured Hosts')
            details['hosts'] = ' | '.join(hosts)

            # Extract artists
            artists = self._extract_participants(soup, 'Featured Artists')
            details['artists'] = ' | '.join(artists)

            return details

        except Exception as e:
            print(f"Error extracting details from {url}: {e}")
            return {
                'number': '',
                'address': '',
                'hosts': '',
                'artists': ''
            }

    def _extract_participants(self, soup: BeautifulSoup, section_title: str) -> List[str]:
        """
        Extract hosts or artists from a section
        Returns list of formatted HTML strings with image and link
        """
        participants = []

        # Find the section by h2 title
        section = None
        for h2 in soup.find_all('h2'):
            if section_title in h2.get_text():
                # Go up to find the container
                section = h2.find_parent('div', class_='e-con-inner')
                break

        if not section:
            return participants

        # Find all participant items
        items = section.find_all('div', class_='jet-listing-grid__item')

        for item in items:
            # Get name and link
            name_h2 = item.find('h2', class_='elementor-heading-title')
            if not name_h2:
                continue

            name = name_h2.get_text().strip()

            # Get link
            link_a = name_h2.find('a')
            participant_url = link_a.get('href', '') if link_a else ''

            # Get image
            img = item.find('img')
            img_src = img.get('src', '') if img else ''

            # Format as: <a href="url"><img src="img_src">Name</a>
            if participant_url and img_src:
                formatted = f'<a href="{participant_url}"><img src="{img_src}">{name}</a>'
                participants.append(formatted)
            elif participant_url:
                # No image, just link
                formatted = f'<a href="{participant_url}">{name}</a>'
                participants.append(formatted)
            else:
                # No link, just name
                participants.append(name)

        return participants

    def scrape_all_locations(self, output_file: str = 'austin_studio_tour_details.csv',
                            max_locations: int = None):
        """
        Scrape all locations and save to CSV
        """
        # Get all location URLs
        locations = self.get_all_location_urls()

        if max_locations:
            locations = locations[:max_locations]
            print(f"Limiting to first {max_locations} locations for testing\n")

        total = len(locations)
        results = []

        print(f"Scraping {total} location pages...")
        print("(This will take a while with 0.5s delay between requests)\n")

        for i, loc in enumerate(locations, 1):
            if i % 10 == 0 or i == total:
                print(f"Progress: {i}/{total}...")

            details = self.extract_location_details(loc['url'])
            details['url'] = loc['url']
            results.append(details)

            # Rate limiting - 0.5 second delay
            time.sleep(0.5)

        # Save to CSV
        self.save_to_csv(results, output_file)

        return results

    def save_to_csv(self, locations: List[Dict[str, str]], filename: str):
        """
        Save locations to CSV file
        """
        if not locations:
            print("No locations to save!")
            return

        print(f"\nSaving {len(locations)} locations to {filename}...")

        fieldnames = ['number', 'address', 'hosts', 'artists', 'url']

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(locations)

        print(f"✓ Successfully saved to {filename}")

        # Show statistics
        with_addresses = sum(1 for loc in locations if loc['address'])
        with_hosts = sum(1 for loc in locations if loc['hosts'])
        with_artists = sum(1 for loc in locations if loc['artists'])

        print(f"\nStatistics:")
        print(f"  Locations with addresses: {with_addresses}/{len(locations)}")
        print(f"  Locations with hosts: {with_hosts}/{len(locations)}")
        print(f"  Locations with artists: {with_artists}/{len(locations)}")


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape Austin Studio Tour location details')
    parser.add_argument('--max-locations', type=int, default=None,
                        help='Maximum number of locations to process (for testing)')
    parser.add_argument('--output', type=str, default='austin_studio_tour_details.csv',
                        help='Output CSV filename')

    args = parser.parse_args()

    print("=" * 70)
    print("Austin Studio Tour Location Details Scraper")
    print("=" * 70)
    print()

    scraper = LocationDetailsScraper()
    results = scraper.scrape_all_locations(
        output_file=args.output,
        max_locations=args.max_locations
    )

    if results:
        print("\n✓ Scraping complete!")
        print("\nSample location:")
        sample = results[0]
        print(f"  Number: {sample['number']}")
        print(f"  Address: {sample['address']}")
        print(f"  Hosts: {sample['hosts'][:100]}..." if len(sample['hosts']) > 100 else f"  Hosts: {sample['hosts']}")
        print(f"  Artists: {sample['artists'][:100]}..." if len(sample['artists']) > 100 else f"  Artists: {sample['artists']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

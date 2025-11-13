#!/usr/bin/env python3
"""
Generate KML file from Austin Studio Tour location data.
Takes a list of location numbers and outputs a KML file for Google Maps.
"""

import csv
import argparse
import re
import sys
from typing import Dict, List, Optional
from html.parser import HTMLParser
from xml.sax.saxutils import escape


class MissingCoordinatesError(Exception):
    """Raised when a requested location is missing coordinates"""
    pass


def extract_links_from_html(html_string: str) -> List[tuple]:
    """Extract clean links from HTML, returning list of (text, url) tuples."""
    if not html_string:
        return []

    # Pattern to match: <a href="url"><img ...>text</a>
    # We want to extract the url and text
    pattern = r'<a\s+href="([^"]+)"[^>]*>(?:<img[^>]*>)?([^<]+)</a>'
    matches = re.findall(pattern, html_string)

    # Return list of (text, url) tuples, stripping whitespace from text
    return [(text.strip(), url) for url, text in matches if text.strip()]


def create_clean_html_links(items_string: str) -> List[str]:
    """Parse HTML items string and return list of clean HTML links."""
    if not items_string:
        return []

    # Split on pipe delimiter
    items = [item.strip() for item in items_string.split('|')]

    clean_links = []
    for item in items:
        links = extract_links_from_html(item)
        for text, url in links:
            clean_links.append(f'<a href="{escape(url)}">{escape(text)}</a>')

    return clean_links


def read_locations_csv(filepath: str) -> Dict[int, dict]:
    """Read location coordinates from CSV file."""
    locations = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract location number from title (e.g., "Location 122" -> 122)
            title = row['title']
            if title.startswith('Location '):
                try:
                    location_num = int(title.replace('Location ', ''))
                    locations[location_num] = {
                        'address': row['address'],
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'url': row['url']
                    }
                except ValueError:
                    continue
    return locations


def read_details_csv(filepath: str) -> Dict[int, dict]:
    """Read location details (hosts and artists) from CSV file."""
    details = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                location_num = int(row['number'])
                details[location_num] = {
                    'hosts': row['hosts'],
                    'artists': row['artists']
                }
            except (ValueError, KeyError):
                continue
    return details


def create_description_html(location_num: int, details: Optional[dict], location_url: str) -> str:
    """Create HTML description for KML placemark."""
    html_parts = [f'<h3>Location {location_num}</h3>']
    sections = []

    if details:
        # Process hosts
        if details.get('hosts'):
            host_links = create_clean_html_links(details['hosts'])
            if host_links:
                host_html = '<p><strong>Hosts:</strong><br/>' + '<br/>'.join(host_links) + '</p>'
                sections.append(host_html)

        # Process artists
        if details.get('artists'):
            artist_links = create_clean_html_links(details['artists'])
            if artist_links:
                artist_html = '<p><strong>Artists:</strong><br/>' + '<br/>'.join(artist_links) + '</p>'
                sections.append(artist_html)

    # Add sections with separators
    if sections:
        html_parts.append('<hr/>'.join(sections))
        html_parts.append('<hr/>')

    # Add view location link
    html_parts.append(f'<p><a href="{escape(location_url)}">View on ATX Studio Tour</a></p>')

    return ''.join(html_parts)


def generate_kml(location_numbers: List[int], locations: Dict[int, dict],
                 details: Dict[int, dict], output_file: str) -> None:
    """
    Generate KML file for specified locations.

    Raises:
        MissingCoordinatesError: If any requested location is not found or missing coordinates
    """

    # Validate all locations have coordinates before generating KML
    for location_num in location_numbers:
        if location_num not in locations:
            raise MissingCoordinatesError(
                f"Location {location_num} not found in locations data. "
                f"Please check that the location exists in the CSV file."
            )

        location = locations[location_num]

        if not location['latitude'] or not location['longitude']:
            raise MissingCoordinatesError(
                f"Location {location_num} has no coordinates. "
                f"Address: {location.get('address', 'N/A')}. "
                f"Please run geocode_addresses.py to geocode this location first."
            )

    kml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '<Document>',
        '<name>Austin Studio Tour Locations</name>',
        '<description>Selected locations from the Austin Studio Tour</description>',
    ]

    for location_num in location_numbers:
        location = locations[location_num]
        location_details = details.get(location_num)
        description_html = create_description_html(
            location_num,
            location_details,
            location['url']
        )

        kml_parts.extend([
            '<Placemark>',
            f'<name>Location {location_num}</name>',
            f'<description><![CDATA[{description_html}]]></description>',
            '<Point>',
            f'<coordinates>{location["longitude"]},{location["latitude"]},0</coordinates>',
            '</Point>',
            '</Placemark>',
        ])

    kml_parts.extend([
        '</Document>',
        '</kml>'
    ])

    # Write KML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(kml_parts))

    print(f"\nKML file generated: {output_file}")
    print(f"Included {len(location_numbers)} location(s)")


def main():
    parser = argparse.ArgumentParser(
        description='Generate KML file from Austin Studio Tour locations'
    )
    parser.add_argument(
        'locations',
        type=int,
        nargs='+',
        help='Location numbers to include in the KML file'
    )
    parser.add_argument(
        '-o', '--output',
        default='studio_tour_locations.kml',
        help='Output KML file path (default: studio_tour_locations.kml)'
    )
    parser.add_argument(
        '--locations-csv',
        default='austin_studio_tour_locations.csv',
        help='Path to locations CSV file'
    )
    parser.add_argument(
        '--details-csv',
        default='austin_studio_tour_details.csv',
        help='Path to details CSV file'
    )

    args = parser.parse_args()

    try:
        print(f"Reading location data...")
        locations = read_locations_csv(args.locations_csv)
        print(f"Found {len(locations)} locations with coordinates")

        print(f"Reading details data...")
        details = read_details_csv(args.details_csv)
        print(f"Found {len(details)} locations with details")

        print(f"\nGenerating KML for locations: {', '.join(map(str, args.locations))}")
        generate_kml(args.locations, locations, details, args.output)

    except MissingCoordinatesError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

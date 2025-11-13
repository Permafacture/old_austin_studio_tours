#!/usr/bin/env python3
"""
Geocode addresses from austin_studio_tour_details.csv and add lat/long to austin_studio_tour_locations.csv
Uses the Nominatim API with proper rate limiting (1 request per second)
"""

import csv
import time
import requests
import json
import re
from typing import Optional, Tuple
import sys


class GeocodeError(Exception):
    """Custom exception for geocoding errors"""
    pass


def remove_unit_info(address: str) -> str:
    """
    Remove suite/unit information from address as it often causes geocoding failures

    Args:
        address: The original address

    Returns:
        Address with suite/unit info removed
    """
    # Pattern to match suite/unit information
    # Matches: ", Ste 123", ", Suite B-4", ", Unit 106", etc.
    pattern = r',\s*(Ste|Suite|Unit|Apt|Apartment|#)\s+[A-Z0-9-]+(?:,|$)'
    cleaned = re.sub(pattern, ',', address, flags=re.IGNORECASE)

    # Clean up any double commas or trailing commas
    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = re.sub(r',\s*$', '', cleaned)

    return cleaned.strip()


def geocode_address(address: str, user_agent: str = "AustinStudioTourGeocoder/1.0") -> Optional[Tuple[float, float]]:
    """
    Geocode an address using Nominatim API
    If initial geocoding fails, tries again without suite/unit information

    Args:
        address: The address to geocode
        user_agent: User agent string for the API request

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    if not address or address.strip() == "":
        return None

    # Nominatim API endpoint
    url = "https://nominatim.openstreetmap.org/search"

    # Headers with custom User-Agent
    headers = {
        'User-Agent': user_agent,
        'Referer': 'https://github.com/Permafacture/old_austin_studio_tours'
    }

    # Try geocoding with the full address first
    addresses_to_try = [address]

    # If address contains suite/unit info, also try without it
    cleaned_address = remove_unit_info(address)
    if cleaned_address != address:
        addresses_to_try.append(cleaned_address)

    for attempt, addr in enumerate(addresses_to_try):
        # Add delay before retry attempt to respect rate limit
        if attempt > 0:
            time.sleep(1.0)

        # Parameters for the request
        params = {
            'q': addr,
            'format': 'jsonv2',
            'limit': 1,
            'addressdetails': 1
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            results = response.json()

            if results and len(results) > 0:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])
                if attempt > 0:
                    print(f"  ℹ Succeeded without suite/unit info", file=sys.stderr)
                return (lat, lon)

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error geocoding {addr}: {e}", file=sys.stderr)
            return None
        except (KeyError, ValueError, IndexError) as e:
            print(f"  ✗ Error parsing response for {addr}: {e}", file=sys.stderr)
            return None

    print(f"  ⚠ No results found for: {address}", file=sys.stderr)
    return None


def load_addresses_from_details(details_csv_path: str) -> dict:
    """
    Load addresses from austin_studio_tour_details.csv

    Returns:
        Dictionary mapping location number to address
    """
    addresses = {}

    with open(details_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            number = row.get('number', '').strip()
            address = row.get('address', '').strip()

            if number and address:
                addresses[number] = address

    return addresses


def update_locations_csv(locations_csv_path: str, addresses: dict, rate_limit_seconds: float = 1.0):
    """
    Update austin_studio_tour_locations.csv with geocoded coordinates

    Args:
        locations_csv_path: Path to the locations CSV file
        addresses: Dictionary mapping location number to address
        rate_limit_seconds: Seconds to wait between API requests
    """
    # Read the existing locations CSV
    rows = []
    with open(locations_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            rows.append(row)

    # Process each row
    geocoded_count = 0
    skipped_count = 0
    error_count = 0

    for i, row in enumerate(rows):
        # Extract location number from title (e.g., "Location 319" -> "319")
        title = row.get('title', '')
        location_num = title.replace('Location ', '').strip()

        # Check if we already have coordinates
        existing_lat = row.get('latitude', '').strip()
        existing_lon = row.get('longitude', '').strip()

        if existing_lat and existing_lon:
            print(f"[{i+1}/{len(rows)}] Skipping {title} - already has coordinates")
            skipped_count += 1
            continue

        # Get address for this location
        address = addresses.get(location_num)

        if not address:
            print(f"[{i+1}/{len(rows)}] Skipping {title} - no address found")
            skipped_count += 1
            continue

        print(f"[{i+1}/{len(rows)}] Geocoding {title}: {address}")

        # Geocode the address
        coords = geocode_address(address)

        if coords:
            lat, lon = coords
            row['latitude'] = str(lat)
            row['longitude'] = str(lon)
            row['address'] = address
            print(f"  ✓ Found: {lat}, {lon}")
            geocoded_count += 1
        else:
            error_count += 1
            # Still add the address even if geocoding failed
            row['address'] = address

        # Rate limiting - wait 1 second between requests
        if i < len(rows) - 1:  # Don't wait after the last request
            time.sleep(rate_limit_seconds)

    # Write updated data back to CSV
    with open(locations_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Print summary
    print("\n" + "="*60)
    print("Geocoding Summary:")
    print(f"  Successfully geocoded: {geocoded_count}")
    print(f"  Skipped (already had coords): {skipped_count}")
    print(f"  Errors/Not found: {error_count}")
    print(f"  Total processed: {len(rows)}")
    print("="*60)


def main():
    """Main function"""
    details_csv = 'austin_studio_tour_details.csv'
    locations_csv = 'austin_studio_tour_locations.csv'

    print("Austin Studio Tour Geocoder")
    print("="*60)
    print(f"Reading addresses from: {details_csv}")
    print(f"Updating coordinates in: {locations_csv}")
    print(f"Rate limit: 1 request per second")
    print("="*60 + "\n")

    # Load addresses
    print("Loading addresses...")
    addresses = load_addresses_from_details(details_csv)
    print(f"Loaded {len(addresses)} addresses\n")

    # Update locations with geocoded data
    print("Starting geocoding...")
    update_locations_csv(locations_csv, addresses)

    print("\nDone!")


if __name__ == '__main__':
    main()

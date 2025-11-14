#!/usr/bin/env python3
"""
Generate separate KML files for each classification category.
Creates one KML per classification type plus one for unclassified locations.
"""

import csv
import argparse
from collections import defaultdict
from typing import Dict, List, Set
from generate_kml import (
    read_locations_csv,
    read_details_csv,
    generate_kml,
    MissingCoordinatesError
)


def read_classifications_csv(filepath: str) -> Dict[str, List[int]]:
    """
    Read location classifications from CSV file.
    Returns dict mapping classification -> list of location numbers.
    """
    classifications = defaultdict(list)
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                location_num = int(row['location'])
                classification = row['classification'].strip()
                if classification:  # Skip empty classifications
                    classifications[classification].append(location_num)
            except (ValueError, KeyError):
                continue
    return dict(classifications)


def filter_locations_with_coordinates(
    location_nums: List[int],
    locations: Dict[int, dict]
) -> List[int]:
    """
    Filter location list to only include those with valid coordinates.
    """
    valid_locations = []
    for loc_num in location_nums:
        if loc_num in locations:
            location = locations[loc_num]
            if location['latitude'] and location['longitude']:
                valid_locations.append(loc_num)
    return valid_locations


def generate_kml_with_custom_name(
    location_numbers: List[int],
    locations: Dict[int, dict],
    details: Dict[int, dict],
    output_file: str,
    document_name: str,
    icon_url: str = None
) -> None:
    """
    Generate KML file with custom document name and optional icon.
    Wraps generate_kml and temporarily modifies the output.

    Args:
        icon_url: URL to the icon image to use for markers
    """
    import tempfile
    import shutil

    if not location_numbers:
        print(f"  No valid locations with coordinates for {output_file}, skipping")
        return

    # Generate KML to a temp file first
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.kml') as tmp:
        tmp_path = tmp.name

    try:
        # Generate using existing function
        generate_kml(location_numbers, locations, details, tmp_path)

        # Read and modify the document name and add icon style
        with open(tmp_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace the default name
        content = content.replace(
            '<name>Austin Studio Tour Locations</name>',
            f'<name>{document_name}</name>'
        )

        # Add icon style if specified
        if icon_url:
            style_section = f'''<Style id="customStyle">
<IconStyle>
<Icon>
<href>{icon_url}</href>
</Icon>
</IconStyle>
</Style>
'''
            # Insert style after Document description tag (first occurrence only)
            content = content.replace(
                '</description>\n<Placemark>',
                f'</description>\n{style_section}<Placemark>',
                1
            )

            # Add styleUrl to each Placemark
            content = content.replace(
                '<Placemark>\n<name>',
                '<Placemark>\n<styleUrl>#customStyle</styleUrl>\n<name>'
            )

        # Write to final destination
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  Generated: {output_file} ({len(location_numbers)} locations)")

    finally:
        import os
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def main():
    parser = argparse.ArgumentParser(
        description='Generate KML files organized by classification'
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
    parser.add_argument(
        '--classification-csv',
        default='location_classification.csv',
        help='Path to classification CSV file'
    )
    parser.add_argument(
        '--output-prefix',
        default='studio_tour_',
        help='Prefix for output KML files'
    )

    args = parser.parse_args()

    print("Reading data files...")
    locations = read_locations_csv(args.locations_csv)
    print(f"  Found {len(locations)} locations with coordinates")

    details = read_details_csv(args.details_csv)
    print(f"  Found {len(details)} locations with details")

    classifications = read_classifications_csv(args.classification_csv)
    print(f"  Found {sum(len(locs) for locs in classifications.values())} classified locations")
    print(f"  Classifications: {', '.join(sorted(classifications.keys()))}")

    # Get set of all classified location numbers
    classified_nums: Set[int] = set()
    for locs in classifications.values():
        classified_nums.update(locs)

    # Find unclassified locations (in locations CSV but not classified)
    all_location_nums = set(locations.keys())
    unclassified_nums = sorted(all_location_nums - classified_nums)

    # Icon mapping for classifications using Google's standard dot markers
    icon_map = {
        'group': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
        'hang': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
        'cool': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
        'complex': 'http://maps.google.com/mapfiles/ms/icons/orange-dot.png',
        'unclassified': 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png'  # Yellow for beige
    }

    print(f"\nGenerating KML files...")

    # Generate KML for each classification
    for classification, location_nums in sorted(classifications.items()):
        # Filter to only locations with valid coordinates
        valid_locs = filter_locations_with_coordinates(location_nums, locations)
        skipped = len(location_nums) - len(valid_locs)
        if skipped > 0:
            print(f"  {classification}: Skipping {skipped} location(s) without coordinates")

        output_file = f"{args.output_prefix}{classification}.kml"
        document_name = f"Austin Studio Tour - {classification.title()} Locations"
        icon_url = icon_map.get(classification)

        generate_kml_with_custom_name(
            valid_locs,
            locations,
            details,
            output_file,
            document_name,
            icon_url
        )

    # Generate KML for unclassified locations
    valid_unclassified = filter_locations_with_coordinates(unclassified_nums, locations)
    skipped_unclassified = len(unclassified_nums) - len(valid_unclassified)
    if skipped_unclassified > 0:
        print(f"  unclassified: Skipping {skipped_unclassified} location(s) without coordinates")

    output_file = f"{args.output_prefix}unclassified.kml"
    document_name = "Austin Studio Tour - Unclassified Locations"

    generate_kml_with_custom_name(
        valid_unclassified,
        locations,
        details,
        output_file,
        document_name,
        icon_map['unclassified']
    )

    print("\n✓ All KML files generated successfully!")


if __name__ == '__main__':
    main()

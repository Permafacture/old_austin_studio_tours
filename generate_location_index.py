#!/usr/bin/env python3
"""Generate an HTML document with links to all locations in order."""

import csv
from pathlib import Path


def generate_html():
    """Generate HTML index of all locations."""
    csv_file = Path(__file__).parent / "austin_studio_tour_details.csv"
    output_file = Path(__file__).parent / "location_index.html"

    # Read locations from CSV
    locations = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            locations.append(row)

    # Sort by location number (ascending)
    locations.sort(key=lambda x: int(x['number']))

    # Generate minimal HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Austin Studio Tour - All Locations</title>
</head>
<body>
<h1>Austin Studio Tour - All Locations</h1>
<p>Total: """ + str(len(locations)) + """ locations</p>

"""

    # Add each location as one line
    for loc in locations:
        number = loc['number']
        url = loc['url']
        address = loc['address'] if loc['address'] else ""

        # Create one line per location
        line = f"Location {number}"
        if address:
            line += f" - {address}"

        html += f'<a href="{url}">{line}</a><br>\n'

    html += """
</body>
</html>
"""

    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Generated {output_file}")
    print(f"✓ Total locations: {len(locations)}")
    print(f"✓ Location range: {locations[0]['number']} - {locations[-1]['number']}")


if __name__ == "__main__":
    generate_html()

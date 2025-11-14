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

    # Generate HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Austin Studio Tour - All Locations</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        .location-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .location-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .location-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .location-number {
            font-size: 1.5em;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 10px;
        }
        .location-address {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            min-height: 40px;
        }
        .location-link {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.9em;
            transition: background 0.2s;
        }
        .location-link:hover {
            background: #0056b3;
        }
        .details {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            font-size: 0.85em;
        }
        .details-label {
            font-weight: bold;
            color: #555;
            margin-top: 8px;
        }
        .details img {
            max-width: 40px;
            max-height: 40px;
            vertical-align: middle;
            margin-right: 5px;
        }
        .stats {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stats p {
            margin: 5px 0;
            color: #666;
        }
    </style>
</head>
<body>
    <h1>Austin Studio Tour - All Locations</h1>

    <div class="stats">
        <p><strong>Total Locations:</strong> """ + str(len(locations)) + """</p>
        <p><strong>Location Numbers:</strong> """ + str(locations[0]['number']) + """ - """ + str(locations[-1]['number']) + """</p>
    </div>

    <div class="location-grid">
"""

    # Add each location
    for loc in locations:
        number = loc['number']
        address = loc['address'] if loc['address'] else "Address not available"
        url = loc['url']
        hosts = loc['hosts']
        artists = loc['artists']

        html += f"""        <div class="location-card">
            <div class="location-number">Location {number}</div>
            <div class="location-address">{address}</div>
            <a href="{url}" class="location-link" target="_blank">View Location →</a>
"""

        # Add hosts if present
        if hosts:
            html += """            <div class="details">
                <div class="details-label">Hosts:</div>
                <div>""" + hosts + """</div>
            </div>
"""

        # Add artists if present
        if artists:
            html += """            <div class="details">
                <div class="details-label">Artists:</div>
                <div>""" + artists + """</div>
            </div>
"""

        html += """        </div>
"""

    html += """    </div>
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

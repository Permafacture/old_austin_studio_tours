# Geocoding Script

This script adds latitude and longitude coordinates to the Austin Studio Tour location data using the Nominatim geocoding API.

## Features

- Geocodes addresses from `austin_studio_tour_details.csv`
- Updates `austin_studio_tour_locations.csv` with latitude/longitude coordinates
- Respects Nominatim's rate limit (1 request per second)
- Automatically retries failed addresses without suite/unit information
- Skips locations that already have coordinates
- Provides detailed progress and summary statistics

## Requirements

- Python 3.6+
- `requests` library

Install dependencies:
```bash
pip install requests
```

## Usage

Simply run the script from the project directory:

```bash
python3 geocode_addresses.py
```

The script will:
1. Load addresses from `austin_studio_tour_details.csv`
2. Read existing data from `austin_studio_tour_locations.csv`
3. Geocode each address that doesn't already have coordinates
4. Update the CSV file with the new coordinates
5. Display a summary of results

## How It Works

1. **Address Loading**: Reads addresses from the details CSV
2. **Smart Geocoding**:
   - First tries the full address with suite/unit numbers
   - If that fails, automatically retries without suite/unit info
3. **Rate Limiting**: Waits 1.1 seconds between API requests to comply with Nominatim usage policy
4. **Progress Tracking**: Shows real-time progress and results for each location
5. **Resume Support**: Skips locations that already have coordinates, so you can safely re-run the script

## API Compliance

The script follows Nominatim's usage requirements:
- 1 request per 1.1 seconds (conservative rate limiting)
- Custom User-Agent: `AustinStudioTourGeocoder/1.0`
- Valid Referer header pointing to the GitHub repository

## Output

The script updates `austin_studio_tour_locations.csv` with:
- `latitude`: Decimal latitude coordinate
- `longitude`: Decimal longitude coordinate
- `address`: The address that was geocoded

## Example Output

```
Austin Studio Tour Geocoder
============================================================
Reading addresses from: austin_studio_tour_details.csv
Updating coordinates in: austin_studio_tour_locations.csv
Rate limit: 1 request per 1.1 seconds
============================================================

Loading addresses...
Loaded 311 addresses

Starting geocoding...
[1/317] Geocoding Location 319: 111 E 8th St, Austin, TX 78701, USA
  ✓ Found: 30.2697587, -97.7418995
[2/317] Geocoding Location 318: 906 E 5th St, Ste 109, Austin, TX 78702
  ℹ Succeeded without suite/unit info
  ✓ Found: 30.2642994, -97.7275992
...

============================================================
Geocoding Summary:
  Successfully geocoded: 280
  Skipped (already had coords): 20
  Errors/Not found: 17
  Total processed: 317
============================================================
```

## Troubleshooting

**No results found**: Some addresses may not be in OpenStreetMap's database. The script will note these but continue processing other addresses.

**Rate limiting errors**: If you see rate limiting errors, the script already waits 1 second between requests. You may need to wait a few minutes before running again.

**Network errors**: The script will report network errors and continue with the next address.

## Data Sources

- **Input**: `austin_studio_tour_details.csv` - Contains scraped address data
- **Output**: `austin_studio_tour_locations.csv` - Updated with coordinates
- **Geocoding API**: [Nominatim](https://nominatim.org/) - OpenStreetMap's geocoding service

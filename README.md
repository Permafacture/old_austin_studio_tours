# Austin Studio Tour Location Scraper

Python script to scrape detailed location data from the Austin Studio Tour website and export to CSV.

## Overview

This project scrapes all 317 locations from the 23rd Annual Austin Studio Tour, extracting:
- Location number
- Physical address
- Featured hosts (with images and links)
- Featured artists (with images and links)

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Scrape all locations (takes ~3 minutes with rate limiting)
python3 scrape_location_details.py

# Test with limited locations
python3 scrape_location_details.py --max-locations 10

# Custom output file
python3 scrape_location_details.py --output my_locations.csv
```

## Output Format

The script generates a CSV file with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| **number** | Location number | 6 |
| **address** | Street address | 710 W Cesar Chavez St, Austin, TX 78701 |
| **hosts** | Pipe-delimited list of hosts with HTML | `<a href="..."><img src="...">The Gallery at Central Library</a>` |
| **artists** | Pipe-delimited list of artists with HTML | `<a href="..."><img src="...">Robin Kang</a>` |
| **url** | Location page URL | https://www.atxstudiotour.com/location/location-6/ |

### HTML Format

Hosts and artists are formatted as HTML with embedded images:
```html
<a href="artist_url"><img src="image_url">Artist Name</a> | <a href="artist2_url"><img src="image2_url">Artist 2</a>
```

Multiple items are separated by ` | ` (pipe with spaces).

## Files

- **`scrape_location_details.py`** - Main scraper script
- **`austin_studio_tour_details.csv`** - Output file with all 317 locations
- `requirements.txt` - Python dependencies
- Old exploration files:
  - `scrape_studios.py` - Initial exploration script
  - `scrape_studios_selenium.py` - Selenium alternative (not needed)
  - `austin_studio_tour_locations.csv` - Basic location list from API

## Statistics

From the complete scrape of all 317 locations:
- **181 locations** have full addresses (57%)
- **120 locations** have featured hosts (38%)
- **286 locations** have featured artists (90%)

Note: Some locations don't have complete information in the expected format on their pages, which is why not all fields are populated for every location.

## Technical Details

### Approach

The script uses plain `requests` and `BeautifulSoup` to:

1. Fetch all location URLs from the WordPress REST API
   - Endpoint: `https://www.atxstudiotour.com/wp-json/wp/v2/location`
   - 317 total locations

2. Visit each location page and extract:
   - Location number from `<h1>` tag
   - Address using regex pattern matching on heading elements
   - Hosts from "Featured Hosts" section (`.jet-listing-grid__item` elements)
   - Artists from "Featured Artists & Art Groups" section

3. For each host/artist, extract:
   - Name from heading element
   - Image URL from `<img src>` attribute
   - Link URL from `<a href>` attribute

### Rate Limiting

The script includes a **0.5 second delay** between requests to avoid overwhelming the server. Scraping all 317 locations takes approximately 3 minutes.

### Why This Approach?

Initially explored using JavaScript rendering (Selenium, requests-html), but discovered that:
- The location pages are rendered server-side (static HTML)
- All needed data is available in the initial HTML response
- No JavaScript execution required
- Much faster and more reliable than browser automation

## Event Information

- **Event:** 23rd Annual Austin Studio Tour
- **Dates:** November 8–9 & 15–16, 2025
- **Time:** 12pm–6pm daily
- **Locations:** 317 venues around Austin, Texas
- **Participants:** 719 artists and art groups
- **Website:** https://www.atxstudiotour.com/

## Example Output

Location 6 (from CSV):

```csv
6,"710 W Cesar Chavez St, Austin, TX 78701","<a href=""https://www.atxstudiotour.com/host/the-gallery-at-central-library/""><img src=""https://www.atxstudiotour.com/wp-content/uploads/2025/10/Robin_Kang_Butterfly_Effect.jpg"">The Gallery at Central Library</a>","<a href=""https://www.atxstudiotour.com/art/robin-kang/""><img src=""https://www.atxstudiotour.com/wp-content/uploads/2025/10/Kang_Firewheel_sm.jpg"">Robin Kang</a>",https://www.atxstudiotour.com/location/location-6/
```

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- lxml

## License

This is a data scraping tool for educational and informational purposes. Please respect the Austin Studio Tour website's terms of service and rate limits.

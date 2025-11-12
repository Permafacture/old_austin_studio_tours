# Austin Studio Tour Map Scraper

Scripts to scrape location data from the Austin Studio Tour website and export to CSV.

## Problem: JavaScript-Rendered Content

The Austin Studio Tour website (`https://www.atxstudiotour.com/explore/?view=map`) uses **JavaScript to dynamically load** map markers, addresses, and coordinates. This means:

- Location addresses are **NOT in the static HTML**
- Coordinates are **NOT available via WordPress REST API**
- Map data is loaded via **AJAX/JavaScript after page load**

## Solutions

### Option 1: requests library (Limited - Location Names Only)

**File:** `scrape_studios.py`

This script uses only the Python `requests` library but has limitations:

```bash
python3 scrape_studios.py
```

**What it gets:**
- ✅ 317 location IDs
- ✅ Location names
- ✅ Location URLs
- ✅ Location types
- ❌ No addresses
- ❌ No coordinates

**Output:** `austin_studio_tour_locations.csv` (without addresses/coordinates)

### Option 2: Selenium (Full Data)

**File:** `scrape_studios_selenium.py`

This script uses Selenium to execute JavaScript and extract full location data.

**Installation:**
```bash
# Install dependencies
pip install selenium webdriver-manager

# For Ubuntu/Debian - install Chrome/Chromium
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
```

**Usage:**
```bash
python3 scrape_studios_selenium.py
```

**What it can get:**
- ✅ Location names
- ✅ Addresses (from individual pages)
- ✅ Coordinates (if available in page data)
- ✅ Full location details

## Files

- `scrape_studios.py` - requests-only version (limited data)
- `scrape_studios_selenium.py` - Selenium version (full data, requires browser)
- `requirements.txt` - Python package dependencies
- `austin_studio_tour_locations.csv` - Output CSV file

## Technical Details

### What We Discovered

1. **WordPress REST API Available:**
   - `/wp-json/wp/v2/location` - Returns basic location posts
   - Does NOT include custom meta fields (address, coordinates)
   - Total: 317 locations

2. **Custom Post Types:**
   - `location` - Studio locations
   - `host` - Event hosts
   - `art` - Artists and art groups
   - `tour` - Tour information

3. **Map Implementation:**
   - Uses JetEngine WordPress plugin
   - Google Maps integration
   - Markers loaded via JavaScript
   - Address geocoding happens client-side

4. **Data Structure:**
   - Location pages exist at: `/location/location-{number}/`
   - Addresses are rendered in the page after JavaScript execution
   - Coordinates stored but not exposed via API

### Why requests Alone Isn't Enough

The website uses modern JavaScript frameworks that render content dynamically:

```javascript
// Data is loaded like this (after page load):
JetEngine.ajax({
    action: 'get_map_markers',
    // ...
});
```

The `requests` library fetches only the initial HTML, which doesn't contain the dynamically loaded content.

## Data Schema

The CSV output includes these fields:

| Field | Description | Example |
|-------|-------------|---------|
| id | WordPress post ID | 14004 |
| title | Location name | Location 319 |
| address | Full street address | 111 E 8th St, Austin, TX 78701, USA |
| latitude | Latitude coordinate | 30.2672 |
| longitude | Longitude coordinate | -97.7431 |
| location_type | Type of venue | [13] (Pop-up) |
| url | Location page URL | https://www.atxstudiotour.com/location/location-319/ |

## Recommendations

1. **For quick location list:** Use `scrape_studios.py` (requests only)
2. **For full data with addresses:** Use `scrape_studios_selenium.py` (Selenium)
3. **For production use:** Consider caching results and rate limiting

## Rate Limiting

Both scripts include rate limiting to be respectful to the server:
- 0.2 second delay between individual page requests
- Progress indicators for long-running operations

## Event Details

- **Event:** 23rd Annual Austin Studio Tour
- **Dates:** November 8–9 & 15–16, 2025
- **Time:** 12pm–6pm daily
- **Locations:** 317 venues around Austin, Texas
- **Participants:** 719 artists and art groups

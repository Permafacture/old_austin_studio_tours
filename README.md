# Austin Studio Tour Map Scraper

Scripts to scrape location data from the Austin Studio Tour website and export to CSV.

## Problem: JavaScript-Rendered Content

The Austin Studio Tour website (`https://www.atxstudiotour.com/explore/?view=map`) uses **JavaScript to dynamically load** map markers, addresses, and coordinates. This means:

- Location addresses are **NOT in the static HTML**
- Coordinates are **NOT available via WordPress REST API**
- Map data is loaded via **AJAX/JavaScript after page load**

## Solutions (3 Options)

### ⭐ Option 1: Enhanced Scraper - RECOMMENDED (scrape_studios_enhanced.py)

**Best balance of performance and functionality**

This script uses `requests-html` for lightweight JavaScript execution - much faster than Selenium, simpler to set up.

**Installation:**
```bash
pip install requests-html
```

**Usage:**
```bash
# Basic data only (fast, no addresses)
python3 scrape_studios_enhanced.py

# With addresses (slower, renders JavaScript)
python3 scrape_studios_enhanced.py --with-addresses

# Test with first 10 locations
python3 scrape_studios_enhanced.py --with-addresses --max-locations 10

# Custom output file
python3 scrape_studios_enhanced.py --with-addresses --output my_locations.csv
```

**What it gets:**
- ✅ 317 location IDs and names
- ✅ Location URLs and types
- ✅ Addresses (with --with-addresses flag)
- ✅ Coordinates if available (with --with-addresses flag)

**Performance:**
- Basic mode: ~5 seconds for all 317 locations
- With addresses: ~10-15 minutes for all locations (includes JS rendering)

### Option 2: Requests-only Version (scrape_studios.py)

**Fastest but limited - no addresses**

Uses only the Python `requests` library:

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

### Option 3: Selenium Version (scrape_studios_selenium.py)

**Most reliable but heaviest**

Full browser automation with Selenium.

**Installation:**
```bash
pip install selenium webdriver-manager

# For Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
```

**Usage:**
```bash
python3 scrape_studios_selenium.py
```

**What it can get:**
- ✅ All location details
- ✅ Addresses
- ✅ Coordinates
- ✅ Full venue details

## Comparison

| Feature | Enhanced (requests-html) | Requests-only | Selenium |
|---------|-------------------------|---------------|----------|
| Setup complexity | Easy | Very Easy | Complex |
| Speed | Fast | Very Fast | Slow |
| Addresses | ✅ Yes | ❌ No | ✅ Yes |
| Coordinates | ✅ Yes | ❌ No | ✅ Yes |
| Dependencies | Minimal | Minimal | Heavy (browser) |
| **Recommended** | **✅ YES** | For testing only | If requests-html fails |

## Files

- **`scrape_studios_enhanced.py`** ⭐ - Recommended solution using requests-html
- `scrape_studios.py` - Requests-only version (limited data)
- `scrape_studios_selenium.py` - Selenium version (full data, requires browser)
- `requirements.txt` - Python package dependencies
- `austin_studio_tour_locations.csv` - Output CSV file

## Technical Details

### What We Discovered

1. **WordPress REST API Available:**
   - `/wp-json/wp/v2/location` - Returns basic location posts
   - Does NOT include custom meta fields (address, coordinates)
   - Total: 317 locations
   - Requires session cookies to avoid 403 errors

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
   - Configuration in `JetSmartFilterSettings` JavaScript variable

4. **Data Structure:**
   - Location pages exist at: `/location/location-{number}/`
   - Addresses are rendered in the page after JavaScript execution
   - Coordinates stored but not exposed via API
   - Bot protection requires proper session cookies

### Why requests Alone Isn't Enough

The website uses modern JavaScript frameworks that render content dynamically:

```javascript
// Data is loaded like this (after page load):
JetEngine.ajax({
    action: 'get_map_markers',
    listing_id: '14109',
    query_id: '52'
});
```

The `requests` library fetches only the initial HTML, which doesn't contain the dynamically loaded content.

### Why requests-html Is The Sweet Spot

`requests-html` provides:
- Chromium-based JavaScript execution (same as Selenium)
- Simpler API (like requests)
- Automatic browser download and management
- Much lighter weight than Selenium
- No need to manage WebDriver separately

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

1. **For production use:** Use `scrape_studios_enhanced.py` with `--with-addresses`
2. **For quick testing:** Use `scrape_studios_enhanced.py` without flags (basic data)
3. **If requests-html fails:** Fall back to `scrape_studios_selenium.py`
4. **For CI/CD pipelines:** Use basic mode or cache results

## Rate Limiting

All scripts include rate limiting to be respectful to the server:
- 0.5 second delay between individual page requests (enhanced version)
- 0.2 second delay (original version)
- Progress indicators for long-running operations

## Event Details

- **Event:** 23rd Annual Austin Studio Tour
- **Dates:** November 8–9 & 15–16, 2025
- **Time:** 12pm–6pm daily
- **Locations:** 317 venues around Austin, Texas
- **Participants:** 719 artists and art groups

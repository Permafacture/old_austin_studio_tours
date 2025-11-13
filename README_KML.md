# KML Generation for Austin Studio Tour

## Overview

The `generate_kml.py` script creates KML files from Austin Studio Tour location data that can be uploaded to Google Maps. Each location becomes a point on the map with descriptions containing HTML-formatted links to hosts and artists.

## Usage

```bash
python3 generate_kml.py <location_numbers> [options]
```

### Examples

Generate KML for specific locations:
```bash
python3 generate_kml.py 90 47 122
```

Specify custom output file:
```bash
python3 generate_kml.py 90 122 -o my_locations.kml
```

### Arguments

- `locations` - One or more location numbers to include (required)
- `-o, --output` - Output KML file path (default: `studio_tour_locations.kml`)
- `--locations-csv` - Path to locations CSV file (default: `austin_studio_tour_locations.csv`)
- `--details-csv` - Path to details CSV file (default: `austin_studio_tour_details.csv`)

## KML Format

The generated KML file includes:
- **Placemarks**: One for each location with coordinates
- **Descriptions**: HTML content with:
  - Location number as heading
  - Hosts section with clickable links and images
  - Artists section with clickable links and images
  - Link to the location page on ATX Studio Tour website

## Uploading to Google Maps

1. Go to [Google My Maps](https://www.google.com/mymaps)
2. Create a new map or open an existing one
3. Click "Import" in the layer panel
4. Upload your generated `.kml` file
5. The locations will appear as points with their descriptions

## Data Sources

The script reads from two CSV files:
- `austin_studio_tour_locations.csv` - Contains coordinates and basic location info
- `austin_studio_tour_details.csv` - Contains host and artist information with HTML links

## Notes

- Locations without coordinates will be skipped with a warning
- The script preserves HTML formatting in descriptions for proper display in Google Maps
- Images from the original data are included as `<img>` tags in the descriptions

# Extract ERA5 Climate Data with Python / Rasterio

ERA-5 Raster Extraction

Frank Donnelly, Head of GIS & Data Services

Brown University Library

Dec 16, 2025 / revised Jan 21, 2026

https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview

Overlay geopackage or shapefile of point observations over an ERA-5 raster
of monthly temperature or precipitation, extracts the values from each
band, converts units, and output results to CSV. Also stores the value of a 
specific month / year as a dedicated value that matches a date in the 
input file.

- Monthly Average 2m tempearture is in degrees Kelvin, program converts to Celsius
- Monthly Total precipitation is in meters, program converts to millimeters

 Assumptions:

1. Input files are stored in the input subfolder
2. ERA raster is a monthly grib file of a single variable (temp OR precip)
3. All months for a given time period were downloaded, with no gaps
4. Raster and point files are in the WGS 84 CRS
5. Point file is a geopackage or shapefile
6. Point file includes a unique ID, a name, and an observation date
7. Point observation date is stored as YYYY-MM-DD or DD-MM-YYYY  
8. Points that fall outside the raster are assigned null values
9. Points with an observation date outside the time frame will have
values recorded, but matching date value will be null

<img width="1149" height="705" alt="era5_gis" src="https://github.com/user-attachments/assets/317c17c7-e7ef-4727-a2f2-da38b390762e" />

# -*- coding: utf-8 -*-
"""
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
"""

import os,csv,sys,rasterio
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from rasterio.plot import show
from rasterio.crs import CRS
from datetime import datetime as dt
from datetime import date

""" VARIABLES - MUST UPDATE THESE VALUES """

# Point file, raster file, name of the variable in the raster
point_file='test_points.gpkg'
raster_file='temp_2018_2025_sl.grib'
varname='temp' # 'temp' or 'precip'

# Column names in point file that contain: unique ID, name, and date
obnum='OBS_NUM'
obname='OBS_NAME'
obdate='OBS_DATE'

 #The first period in the ERA data write as YYYY-MM 
startdate='2018-01' # YYYY-MM

# True means dates in point file are YYYY-MM-DD, False means DD-MM-YYYY
standard_date=False # True or False

""" MAIN PROGRAM """

def convert_units(varname,value):
    # Convert temperature from Kelvin to Celsius
    if varname=='temp':
        newval=value-272.15
    # Convert precipitation from meters to millimeters
    elif varname=='precip':
        newval=value*1000
    else:
        newval=value
    return newval

# Estabish paths, read files
yearmonth=np.datetime64(startdate)
point_path=os.path.join('input',point_file)
raster_path=os.path.join('input',raster_file)
outfolder='output'
if not os.path.exists(outfolder):
    os.makedirs(outfolder)
point_data = gpd.read_file(point_path)

# Conditions for exiting the program
if point_data[obnum].is_unique is True:
    pass
else:
    print('\n FAIL: unique ID column in the input file contains duplicate values, cannot proceed.')
    sys.exit()
    
if varname in ('temp','precip'):
    pass
else:
    print('\n FAIL: variable name must be set to either "temp" or "precip"')
    sys.exit()
    
# Dictionary holds results, key is unique ID from point file, value is
# another dictionary with column and observation names as keys
result_dict={}  

# Identify and save the raster row and column for each point
with rasterio.open(raster_path,'r+') as raster:
    raster.crs = CRS.from_epsg(4326)
    for idx in point_data.index:
        xcoord=point_data['geometry'][idx].x
        ycoord=point_data['geometry'][idx].y
        row, col = raster.index(xcoord,ycoord)
        result_dict[point_data[obnum][idx]]={
            obname:point_data[obname][idx],
            obdate:point_data[obdate][idx],
            'RASTER_ROW':row,
            'RASTER_COL':col}
  
# Iterate through raster bands, extract the climate value,
# store in column named for Year-Month, handle points outside the raster
with rasterio.open(raster_path,'r+') as raster:
    raster.crs = CRS.from_epsg(4326)
    for band_index in range(1, raster.count + 1):      
        for k,v in result_dict.items():
            rrow=v['RASTER_ROW']
            rcol=v['RASTER_COL']
            if any ([rrow < 0, rrow >= raster.height,
                    rcol < 0, rcol >= raster.width]):
                result_dict[k]['YM-'+str(yearmonth)]=None
            else:
                climval=raster.read(band_index)[rrow,rcol]
                climval_new=round(convert_units(varname,climval.item()),4)
                result_dict[k]['YM-'+str(yearmonth)]=climval_new
        yearmonth=yearmonth+np.timedelta64(1, 'M')

# Iterate through results, find matching climate value for the
# observation date in the point file, handle dates outside the raster       
for k,v in result_dict.items():
    if standard_date is False: # handles dd-mm-yyyy dates
        formatdate=dt.strptime(v[obdate].strip(),'%m/%d/%Y').date()
        numdate=np.datetime64(formatdate)
    else:
        numdate=v[obdate] # handles yyyy-mm-dd dates
    obyrmonth='YM-'+np.datetime_as_string(numdate, unit='M').item()
    if obyrmonth in v:
        matchdate=v[obyrmonth]
    else:
        matchdate=None
    result_dict[k]['MATCH_VALUE']=matchdate

# Converts dictionary to list for output
firstkey=next(iter(result_dict))
header=list(result_dict[firstkey].keys())
header.insert(0,obnum)
result_list=[header]
for k,v in result_dict.items():
    record=[k]
    for k2, v2 in v.items():
        record.append(v2)
    result_list.append(record)
    
# Plot the points over the first raster that was processed to see visual  
with rasterio.open(raster_path,'r+') as raster:
    raster.crs = CRS.from_epsg(4326)
    fig, ax = plt.subplots(figsize=(12,12))
    point_data.plot(ax=ax, color='black')
    show((raster,1), ax=ax)

# Output results to CSV file    
today=str(date.today())
outfile=varname+'_'+today+'.csv'
outpath=os.path.join(outfolder,outfile)
with open(outpath, 'w', newline='') as writefile:
    writer=csv.writer(writefile, quoting=csv.QUOTE_MINIMAL, delimiter=',')
    writer.writerows(result_list)   

count_r=len(result_list)
count_c=len(result_list[0])  
print('\n Done, wrote {} rows with {} values for {} data to {}'.format(count_r,count_c,varname,outpath))
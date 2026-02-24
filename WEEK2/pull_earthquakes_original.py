import pandas as pd
from obspy import read_events
import obspy
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from datetime import datetime
import ssl
from obspy import read
from obspy import Stream
from obspy import Trace
from obspy import UTCDateTime
#from geopy.distance import geodesic
from obspy.geodetics import gps2dist_azimuth
#import geopy
import numpy as np
import tempfile
import pygmt

def pull_earthquakes(lat, lon, max_rad, start, end, min_mag, array_name, array2_name,lat2,lon2, second_array = True):

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=quakeml&starttime="+start+"&endtime="+end+"&latitude="+lat+"&longitude="+lon+"&maxradiuskm="+max_rad+"&minmagnitude="+min_mag+""

    catalog = read_events(url)
    depths = []
    magnitudes = []
    latitudes = []
    longitudes = []
    times_utc = []
    times_ak = []
    names = []


# Extract data from each event
    for event in catalog:
    # Extract depth
        depth = event.origins[0].depth / 1000  # Depth is in meters, convert to kilometers
    
    # Extract magnitude
        magnitude = event.magnitudes[0].mag
    
    # Extract latitude and longitude
        latitude = event.origins[0].latitude
        longitude = event.origins[0].longitude
    
    # Extract time
        time = event.origins[0].time
    
        resource_id = event.resource_id.id
        name = resource_id.split('?')[-1]
        name = name[:-15]
        name= name[8:]
    
    # Append data to lists
        depths.append(depth)
        magnitudes.append(magnitude)
        latitudes.append(latitude)
        longitudes.append(longitude)
        times_utc.append(time)
        times_ak.append(time - 60*60*8)
        names.append(name)

# Create a DataFrame
    data = {
        'Name': names,
        'Depth (km)': depths,
        'Magnitude': magnitudes,
        'Latitude': latitudes,
        'Longitude': longitudes,
        'Time_utc': times_utc,
        'Time_ak': times_ak,
    }

    df = pd.DataFrame(data)
    sta_lat = float(lat)
    sta_lon = float(lon)

    dist = []
    baz = []
    array = []
    lats = df['Latitude'].to_numpy()
    lons = df['Longitude'].to_numpy()
    for i in range(len(df)):
        dist1, baz1, az = gps2dist_azimuth(lats[i], lons[i], sta_lat, sta_lon)
        dist.append(dist1/1000)
        baz.append(baz1)
        array.append(array_name)

    df[array_name+'_distance(km)'] = dist
    df[array_name+'_backazimuth'] = baz
    df[array_name+'_array'] = array

    if second_array ==True:

        dist = []
        baz = []
        array = []
        lats = df['Latitude'].to_numpy()
        lons = df['Longitude'].to_numpy()
        for i in range(len(df)):
            dist1, baz1, az = gps2dist_azimuth(lats[i], lons[i], float(lat2), float(lon2))
            dist.append(dist1/1000)
            baz.append(baz1)
            array.append(array2_name)

        df[array2_name+'_distance(km)'] = dist
        df[array2_name+'_backazimuth'] = baz
        df[array2_name+'_array'] = array
        
    
    
    

    HOM = df.reset_index()

import pandas as pd
import obspy
import matplotlib.pyplot as plt
import numpy as np
import argparse
from obspy import read
from obspy import read_events
from obspy import Stream
from obspy import Trace
from obspy import UTCDateTime
from datetime import datetime, time, timezone
from obspy.taup import TauPyModel
from obspy.taup import taup_create
from obspy.geodetics import gps2dist_azimuth
from obspy.geodetics import kilometers2degrees
from obspy.signal.util import util_geo_km
from array_functions import calculate_slowness



def pull_earthquakes(lat, lon, max_rad, start, end, min_mag, array_name, velocity_model):

    """
    Pulls in earthquakes from a region based on lat, lon, timing, and magnitude.
    It also returns other values of interest about the event for array processing,
    such as backazimuth, slowness, and epicentral distance to the event.

    Example use:
    
    python pull_earthquakes.py --lat 64.7714 --lon -146.886597 --max_rad 500 \
    --start '2025-10-10' --end '2025-12-10' --min_mag 3.0 --array_name 'ILAR' \
    --velocity_model 'iasp91'

    
    Parameters:
        lat: latitude of array/station (float
        lon: longitude of array/station (float)
        max_rad: maximum radius of earthquakes in kilometers (float)
        start: start time in UTC format (str)
        end: end time in UTC format (str)
        min_mag: minimum magnitude of earthquakes (float)
        array_name: name of array/station (str)
        velocity_model: name of velocity model (ex. 'iasp91', 'ak135')
        
    Returns:
        pandas DataFrame:
           'event_id': event id from USGS catalog
           'depth': depth of earthquake in km
           'magnitude': magnitude of earthquake
           'latitude': earthquake latitude
           'longitude': earthquake longitude
           'time_utc': origin time in UTC
           'time_ak': origin time in AK
           'distance': epicentral distance to event in km
           'backazimuth': backazimuth from array/station to earthquake
           'array': name of station/array
           'slowness': surface slowness (s/km)
           'trace_vel': surface trace velocity (km/s)
           'incident_angle': angle from vertical of first arriving wave (degrees)
           'p_arrival': arrival time of p-wave (seconds)             
    """

    ##Pull data in from FDSNWS: https://earthquake.usgs.gov/fdsnws/event/1/
    url = ('https://earthquake.usgs.gov/fdsnws/event/1/query?format=quakeml&starttime='+start+'&endtime='
           +end+'&latitude='+str(lat)+'&longitude='+str(lon)+'&maxradiuskm='+str(max_rad)+'&minmagnitude='+str(min_mag)+'')

    catalog = read_events(url)
    depths = []
    magnitudes = []
    latitudes = []
    longitudes = []
    times_utc = []
    times_ak = []
    names = []
    distances = []
    backazimuth = []
    array = []
    slowness = []
    trace_vel = []
    incident_angle = []
    p_arrival = []

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

        # Extract event_id
        resource_id = event.resource_id.id
        name = resource_id.split('?')[-1]
        name = name[:-15]
        name= name[8:]

        # Calculate distance, backazimuth
        dist, baz, az = gps2dist_azimuth(latitude, longitude, lat, lon)
        dist = dist/1000 #converts m to km
        
        # Calculate slowness, trace velocity, incident angle, and arrival time
        slow, t_vel, incident, p = calculate_slowness(dist, depth, velocity_model)
        
        # Append data to lists
        depths.append(depth)
        magnitudes.append(magnitude)
        latitudes.append(latitude)
        longitudes.append(longitude)
        times_utc.append(time)
        times_ak.append(time - 60*60*8)  # conversion to AK time
        names.append(name)
        distances.append(dist)
        backazimuth.append(baz)
        array.append(array_name)
        slowness.append(slow)
        trace_vel.append(t_vel)
        incident_angle.append(incident)
        p_arrival.append(p)

    # Combine into DataFrame
    data = {
        'event_id': names,
        'depth': depths,
        'magnitude': magnitudes,
        'latitude': latitudes,
        'longitude': longitudes,
        'time_utc': times_utc,
        'time_ak': times_ak,
        'distance': distances,
        'backazimuth': backazimuth,
        'array': array,
        'slowness': slowness,
        'trace_vel': trace_vel,
        'incident_angle': incident_angle,
        'p_arrival': p_arrival,
    }

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pull earthquakes around a station/array"
    )

    parser.add_argument("--lat", type = float, required = True, help = "Array latitude")
    parser.add_argument("--lon", type = float, required = True, help = "Array longitude")
    parser.add_argument("--max_rad", type = float, required = True, help = "Max radius (km)")
    parser.add_argument("--start", type = str, required = True, help = "Start time (YYYY-MM-DD)")
    parser.add_argument("--end", type = str, required = True, help = "End time (YYYY-MM-DD)")
    parser.add_argument("--min_mag", type = float, required = True, help = "Minimum magnitude")
    parser.add_argument("--array_name", type = str, required = True, help = "Array name")
    parser.add_argument("--velocity_model", type = str, default="iasp91", help = "Velocity model (default: iasp91)",
    )

    args = parser.parse_args()

    df = pull_earthquakes(
        lat=args.lat,
        lon=args.lon,
        max_rad=args.max_rad,
        start=args.start,
        end=args.end,
        min_mag=args.min_mag,
        array_name=args.array_name,
        velocity_model=args.velocity_model,
    )

    print(df)
    print('Number of earthquakes >'+str(args.min_mag)+' within '+str(args.max_rad)+' km:', len(df))
